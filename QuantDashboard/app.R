# ==========================================================
# PACKAGES
# ==========================================================
library(shiny)
library(DBI)
library(RPostgres)
library(tidyquant)
library(dplyr)
library(ggplot2)
library(zoo)
library(scales)
library(bslib)

# List of available assets
ACTIFS_DISPO <- c(
  "Euro / US Dollar" = "EURUSD=X",
  "British Pound / US Dollar" = "GBPUSD=X",
  "Bitcoin / US Dollar" = "BTC-USD",
  "Ethereum / US Dollar" = "ETH-USD",
  "S&P 500 Index" = "^SPX",
  "Apple Inc." = "AAPL"
)

# Utility function to connect to PostgreSQL Neon Cloud
connect_db <- function() {
  dbConnect(
    RPostgres::Postgres(),
    dbname = Sys.getenv("NEON_DB"),
    host = Sys.getenv("NEON_HOST"),
    port = 5432,
    user = Sys.getenv("NEON_USER"),
    password = Sys.getenv("NEON_PWD"),
    sslmode = "require"
  )
}

# ==========================================================
# SHINY UI (Power BI Style Fixed Format)
# ==========================================================
ui <- page_sidebar(
  theme = bs_theme(bootswatch = "flatly"),
  title = "Algorithmic Trading & Multi-Asset Quantitative Dashboard",
  fillable = TRUE, 
  
  tags$head(
    tags$style(HTML("
    /* Fix global container dimensions */
    .bslib-page-sidebar {
      max-width: 1450px !important;
      height: 820px !important;
      margin: 15px auto !important;
      border: 1px solid #e0e0e0;
      box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    /* Top Header Bar styling */
    .navbar {
      padding-top: 8px !important;    
      padding-bottom: 8px !important; 
      min-height: 50px !important;    
    }
    
    .navbar-brand {
      font-size: 1.3rem !important;   
      font-weight: 600 !important;    
    }

    /* Prevent internal card scrollbars */
    .card-body {
      overflow: hidden !important; 
    }
  "))
  ),
  
  sidebar = sidebar(
    title = "Configuration",
    selectInput(
      inputId = "select_actif",
      label = "Select an Asset:",
      choices = ACTIFS_DISPO,
      selected = "EURUSD=X"
    ),
    hr(),
    textOutput("lastDate"),
    p(),
    span("Stack: R Shiny, bslib, PostgreSQL (Neon), Tidyquant", style = "font-size: 0.85em; color: gray;")
  ),
  
  # ROW 1: Main Trend Analysis (Fills space automatically)
  layout_column_wrap(
    width = 1,
    card(
      card_header("Price Trend & Moving Averages (MA)"),
      plotOutput("pricePlot", height = "100%") 
    )
  ),
  
  # ROW 2: Balanced 50/50 Sub-Analyses
  layout_columns(
    col_widths = c(6, 6),
    
    # Left: Returns Histogram
    card(
      card_header("Log Returns Distribution"),
      plotOutput("histPlot", height = "100%") 
    ),
    
    # Right: Quantitative Analytics Table
    card(
      card_header("Key Performance Indicators & Risk Management"),
      tableOutput("kpiTable")
    )
  )
)

# ==========================================================
# SERVER
# ==========================================================
server <- function(input, output, session) {
  
  # Reactive ETL pipeline & data fetching
  get_data <- reactive({
    actif <- input$select_actif
    
    # Dynamic processing notification
    id_notif <- showNotification(
      paste("Updating data and computing metrics for", names(ACTIFS_DISPO[ACTIFS_DISPO == actif])), 
      duration = NULL, 
      type = "message"
    )
    on.exit(removeNotification(id_notif), add = TRUE)
    
    # 1. ETL Pipeline
    tryCatch({
      donnees_internet <- tq_get(actif, from = "2025-01-01", to = Sys.Date())
      
      donnees_propres <- donnees_internet %>%
        select(date, symbol, close, volume) %>%
        rename(rate_date = date, pair_name = symbol, exchange_rate = close, volume_24h = volume)
      
      con <- connect_db()
      existing_data <- tryCatch(dbReadTable(con, "fact_exchange_rates"), error = function(e) NULL)
      
      if (is.null(existing_data)) {
        dbWriteTable(con, "fact_exchange_rates", donnees_propres, overwrite = TRUE, row.names = FALSE)
      } else {
        dbExecute(con, paste0("DELETE FROM fact_exchange_rates WHERE pair_name = '", actif, "'"))
        dbWriteTable(con, "fact_exchange_rates", donnees_propres, append = TRUE, row.names = FALSE)
      }
      dbDisconnect(con)
    }, error = function(e) {
      showNotification("Database sync failed. Using local cache layer.", type = "warning")
    })
    
    # 2. Query filtered asset data from Cloud SQL
    con <- connect_db()
    query <- paste0("SELECT rate_date, exchange_rate FROM fact_exchange_rates WHERE pair_name = '", actif, "' ORDER BY rate_date ASC")
    df <- dbGetQuery(con, query)
    dbDisconnect(con)
    
    req(nrow(df) > 0)
    df$rate_date <- as.Date(df$rate_date)
    
    # 3. Vectorized Quant Feature Engineering
    df <- df %>%
      arrange(rate_date) %>%
      mutate(
        return = c(NA, diff(log(exchange_rate))),
        sma20  = rollmean(exchange_rate, 20, fill = NA, align = "right"),
        sma50  = rollmean(exchange_rate, 50, fill = NA, align = "right"),
        sma200 = rollmean(exchange_rate, 200, fill = NA, align = "right")
      )
    
    df
  })
  
  # Sidebar Meta Updates
  output$lastDate <- renderText({
    paste("Last Available Quote:", max(get_data()$rate_date))
  })
  
  # ===================================
  # OUTPUT: KPI DATAFRAME RENDER
  # ===================================
  output$kpiTable <- renderTable({
    df <- get_data()
    returns <- na.omit(df$return)
    
    last_price <- round(tail(df$exchange_rate, 1), 4)
    
    # 30-Day performance
    if (nrow(df) < 30) {
      perf_30j <- "N/A"
    } else {
      perf <- (tail(df$exchange_rate, 1) / tail(df$exchange_rate, 30)[1] - 1) * 100
      perf_30j <- paste0(ifelse(perf > 0, "+", ""), round(perf, 2), " %")
    }
    
    # Annualized Volatility
    vol <- paste0(round(sd(returns) * sqrt(252) * 100, 2), " %")
    
    # Value at Risk 95% (1-Day)
    var_95 <- paste0(round(quantile(returns, 0.05) * 100, 2), " %")
    
    # Maximum Drawdown
    cummax_price <- cummax(df$exchange_rate)
    drawdown <- (df$exchange_rate / cummax_price - 1)
    max_dd <- paste0(round(min(drawdown) * 100, 2), " %")
    
    # Construct final display table
    data.frame(
      Indicator = c(
        "Last Closing Price", 
        "30-Day Performance", 
        "Annualized Volatility", 
        "Value at Risk (VaR 95% - 1d)", 
        "Maximum Drawdown"
      ),
      Value = c(
        as.character(last_price), 
        perf_30j, 
        vol, 
        var_95, 
        max_dd
      )
    )
  }, striped = TRUE, hovered = TRUE, spacing = "l", align = "ll")
  
  # ===================================
  # OUTPUTS: GGPLOT VISUALIZATIONS
  # ===================================
  output$pricePlot <- renderPlot({
    df <- get_data()
    
    ggplot(df, aes(rate_date, exchange_rate)) +
      geom_line(aes(color = "Closing Price"), linewidth = 1) +
      geom_line(aes(y = sma20, color = "20-Day MA"), linewidth = 0.8, linetype = "dashed") +
      geom_line(aes(y = sma50, color = "50-Day MA"), linewidth = 0.8) +
      geom_line(aes(y = sma200, color = "200-Day MA"), linewidth = 1.1) +
      scale_color_manual(values = c(
        "Closing Price" = "#2c3e50",
        "20-Day MA" = "#e67e22",
        "50-Day MA" = "#2ecc71",
        "200-Day MA" = "#e74c3c"
      )) +
      labs(x = "", y = "Price / Exchange Rate", color = "Indicators") +
      theme_minimal(base_size = 14) +
      theme(legend.position = "bottom")
  })
  
  output$histPlot <- renderPlot({
    ggplot(get_data(), aes(return)) +
      geom_histogram(bins = 40, fill = "#3498db", colour = "white") +
      theme_minimal(base_size = 12) +
      labs(x = "Daily Log Returns", y = "Frequency")
  })
}

# ==========================================================
# INITIALIZE APPLICATION
# ==========================================================
shinyApp(ui = ui, server = server)
