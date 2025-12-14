###############################################################################
# DASHBOARD CATPCA – VERSION CORRIGÉE (sans erreurs Viridis)
###############################################################################

library(shiny)
library(shinythemes)
library(Gifi)
library(ggplot2)
library(dplyr)
library(foreign)
library(plotly)
library(DT)
library("corrplot")

# UI -------------------------------------------------------------------------
ui <- fluidPage(
  theme = shinytheme("flatly"),
  titlePanel("Dashboard CATPCA – Interactif"),
  
  sidebarLayout(
    sidebarPanel(
      h3("Chargement des données"),
      fileInput("file", "Importer un fichier (CSV ou ARFF)",
                accept = c(".csv", ".arff", ".txt")),
      hr(),
      h3("Paramètres CATPCA"),
      uiOutput("var_selector"),
      sliderInput("ndim", "Nombre de dimensions", min = 2, max = 10, value = 3),
      selectInput("dim_plot", "Type de projection",
                  choices = c("2D", "3D"), selected = "2D"),
      actionButton("run", "Lancer CATPCA", class = "btn-primary"),
      hr(),
      h4("Résumé du modèle"),
      verbatimTextOutput("info"),
      hr(),
      uiOutput("dim_selector")
    ),
    
    mainPanel(
      tabsetPanel(
        tabPanel("Projection 2D/3D", plotlyOutput("plot_scores", height = 500)),
        tabPanel("Biplot", plotlyOutput("plot_biplot", height = 500)),
        tabPanel("Loadings", plotlyOutput("plot_loadings", height = 500)),
        tabPanel("Loadings Dim1 vs Dim2", plotlyOutput("plot_loadings2d", height = 500)),
        tabPanel("Cercle des corrélations", plotlyOutput("plot_corr_circle", height = 500)),
        tabPanel("Cercle des corrélations", plotOutput("cor_circle", height = 600)),
        tabPanel("Scree Plot", plotlyOutput("plot_scree", height = 500)),
        tabPanel("Cos²", plotOutput("plot_cos2", height = 600))
        
      )
    )
  )
)

# SERVER ----------------------------------------------------------------------
server <- function(input, output, session) {
  
  # Chargement dataset
  dataset <- reactive({
    req(input$file)
    ext <- tools::file_ext(input$file$name)
    if (ext %in% c("csv", "txt")) read.csv(input$file$datapath)
    else if (ext == "arff") read.arff(input$file$datapath)
    else {
      showNotification("Format non supporté.", type = "error")
      return(NULL)
    }
  })
  
  # Sélecteur variables
  output$var_selector <- renderUI({
    df <- dataset(); req(df)
    checkboxGroupInput("vars", "Variables à inclure :", names(df), selected = names(df))
  })
  
  # Sélecteur dimensions loadings
  output$dim_selector <- renderUI({
    req(input$ndim)
    selectInput("dim_select", "Dimension à visualiser",
                choices = 1:input$ndim, selected = 1)
  })
  
  # CATPCA
  result <- eventReactive(input$run, {
    df <- dataset(); req(df)
    df <- df[, input$vars, drop = FALSE]
    if (ncol(df) < 2) { showNotification("Au moins 2 variables requises.", type="error"); return(NULL) }
    df <- df %>% mutate(across(where(is.character), as.factor))
    
    level_vec <- sapply(df, function(col){
      if (is.ordered(col)) "ordinal"
      else if (is.factor(col)) "nominal"
      else "metric"
    })
    
    withProgress(message = "Calcul CATPCA...", value = 0, {
      tryCatch(princals(df, ndim = input$ndim, level = level_vec),
               error = function(e){ showNotification(e$message, type="error"); NULL })
    })
  })
  
  # Résumé modèle
  output$info <- renderText({
    res <- result(); if (is.null(res)) return("Aucun résultat.")
    paste(capture.output(summary(res)), collapse="\n")
  })
  
  # Projection 2D/3D
  output$plot_scores <- renderPlotly({
    res <- result(); req(res)
    scores <- as.data.frame(res$objectscores)
    colnames(scores) <- paste0("Dim", seq_len(ncol(scores)))
    
    if (input$dim_plot == "2D") {
      p <- ggplot(scores, aes(Dim1, Dim2)) +
        geom_point(color="blue", alpha=.8) +
        theme_minimal() +
        labs(title="Projection CATPCA : individus")
      ggplotly(p)
    } else {
      plot_ly(scores, x=~Dim1, y=~Dim2, z=~Dim3,
              type="scatter3d", mode="markers",
              marker=list(color="blue"))
    }
  })
  
  # Biplot
  output$plot_biplot <- renderPlotly({
    res <- result(); req(res)
    
    scores <- as.data.frame(res$objectscores)
    load <- as.data.frame(res$loadings)
    
    scores$D1 <- scores[,1]; scores$D2 <- scores[,2]
    load$L1 <- load[,1]; load$L2 <- load[,2]
    load$Variable <- rownames(load)
    
    plot_ly() %>%
      add_markers(data=scores, x=~D1, y=~D2,
                  marker=list(color="blue"), name="Individus") %>%
      add_segments(data=load, x=0, y=0, 
                   xend=~L1, yend=~L2,
                   line=list(color="red")) %>%
      add_text(data=load, x=~L1, y=~L2,
               text=~Variable)
  })
  
  # Loadings 1D
  output$plot_loadings <- renderPlotly({
    res <- result(); req(res)
    d <- as.numeric(input$dim_select)
    load <- as.data.frame(res$loadings)
    df <- data.frame(Variable = rownames(load), Value = load[, d])
    
    plot_ly(df, x=~Variable, y=~Value,
            type="scatter", mode="markers+text",
            text=~Variable, textposition="top center",
            marker=list(color="steelblue"))
  })
  
  # Loadings Dim1 vs Dim2
  output$plot_loadings2d <- renderPlotly({
    res <- result(); req(res)
    load <- as.data.frame(res$loadings)
    df <- data.frame(Variable=rownames(load),
                     Dim1=load[,1], Dim2=load[,2])
    
    plot_ly(df, x=~Dim1, y=~Dim2,
            type="scatter", mode="markers+text",
            text=~Variable, textposition="top center",
            marker=list(color="red"))
  })
  
  # Cercle corrélation (Plotly)
  output$plot_corr_circle <- renderPlotly({
    res <- result(); req(res)
    load <- as.data.frame(res$loadings)
    df <- data.frame(Variable=rownames(load),
                     Dim1=load[,1], Dim2=load[,2])
    
    circle <- data.frame(
      x = cos(seq(0, 2*pi, length.out=200)),
      y = sin(seq(0, 2*pi, length.out=200))
    )
    
    plot_ly() %>%
      add_trace(data=circle, x=~x, y=~y,
                type="scatter", mode="lines",
                line=list(color="black")) %>%
      add_segments(x=-1, xend=1, y=0, yend=0,
                   line=list(color="gray70")) %>%
      add_segments(x=0, xend=0, y=-1, yend=1,
                   line=list(color="gray70")) %>%
      add_markers(data=df, x=~Dim1, y=~Dim2,
                  marker=list(color="red", size=10)) %>%
      add_text(data=df, x=~Dim1, y=~Dim2,
               text=~Variable)
  })
  
  # Cercle corrélation (ggplot)
  output$cor_circle <- renderPlot({
    res <- result(); req(res)
    load <- as.data.frame(res$loadings)
    df <- data.frame(var=rownames(load),
                     Dim1=load[,1], Dim2=load[,2])
    
    circle <- data.frame(x = cos(seq(0,2*pi,len=200)),
                         y = sin(seq(0,2*pi,len=200)))
    
    ggplot() +
      geom_path(data=circle, aes(x,y), color="grey40") +
      geom_segment(data=df, aes(x=0,y=0,xend=Dim1,yend=Dim2),
                   arrow=arrow(length=unit(0.2,"cm")),
                   color="blue") +
      geom_text(data=df, aes(x=Dim1, y=Dim2, label=var),
                vjust=-0.5, size=5) +
      coord_equal() +
      theme_minimal() +
      labs(title="Cercle des corrélations",
           x="Dim1", y="Dim2")
  })
  
  # Scree plot unique
  output$plot_scree <- renderPlotly({
    res <- result(); req(res)
    
    eig <- res$evals
    eig <- eig[!is.na(eig)]
    vaf <- eig / sum(eig) * 100
    
    df <- data.frame(
      Dim = 1:length(eig),
      VAF = vaf,
      Cumul = cumsum(vaf)
    )
    
    plot_ly(df) %>%
      add_bars(x=~Dim, y=~VAF,
               name="Variance (%)",
               marker=list(color="blue")) %>%
      add_trace(x=~Dim, y=~Cumul,
                mode="lines+markers",
                name="Cumul (%)")
  })
  
  output$plot_cos2 <- renderPlot({
    res <- result(); 
    req(res)
    
    # loadings CATPCA
    L <- as.data.frame(res$loadings)
    if (is.null(L) || nrow(L)==0){
      showNotification("Loadings indisponibles.", type="error")
      return(NULL)
    }
    
    # cos² = loadings²
    cos2 <- L^2
    rownames(cos2) <- rownames(L)
    colnames(cos2) <- paste0("Dim", 1:ncol(L))
    
    # Corrplot des cos²
    corrplot(as.matrix(cos2), 
             is.corr = FALSE,
             method = "color",
             tl.col = "black",
             tl.cex = 1.1)
  })
  
  
  
  
  
  
  
}

# App lancement --------------------------------------------------------------
shinyApp(ui, server)
