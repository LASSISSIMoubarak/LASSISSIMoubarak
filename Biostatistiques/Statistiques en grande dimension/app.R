library(shiny)

source("gasoline_nir_analysis.R")
gasoline_data <- load_gasoline_data()

ui <- fluidPage(
  titlePanel("NIR Spectra Analysis (PCR, PLS)"),
  sidebarLayout(
    sidebarPanel(
      selectInput(
        "model_type",
        "Model",
        choices = c("PCR" = "PCR", "PLS" = "PLS"),
        selected = "PCR"
      ),
      sliderInput(
        "ncomp",
        "Number of components",
        min = 1,
        max = 20,
        value = 6,
        step = 1
      ),
      sliderInput(
        "train_fraction",
        "Calibration set size (%)",
        min = 50,
        max = 90,
        value = 80,
        step = 5
      ),
      numericInput("seed", "Split seed", value = 4433, min = 1),
      helpText(
        "The gasoline data are provided by the R package pls. Leave-one-out (LOO) is used to asses number of principal component",
        
      )
    ),
    mainPanel(
      h4("Test set results"),
      tableOutput("metrics"),
      tabsetPanel(
        tabPanel("Spectra", plotOutput("spectra", height = 400)),
        tabPanel("Cross-validation", plotOutput("cv", height = 400)),
        tabPanel("Predictions", plotOutput("predictions", height = 400))
      ),
      p(
        class = "text-muted"
      )
    )
  )
)

server <- function(input, output, session) {
  analysis <- reactive({
    tryCatch(
      fit_gasoline_model(
        gasoline_data,
        model_type = input$model_type,
        train_fraction = input$train_fraction / 100,
        seed = input$seed,
        ncomp = input$ncomp
      ),
      error = function(error) {
        showNotification(
          paste("Could not fit the model:", conditionMessage(error)),
          type = "error",
          duration = NULL
        )
        NULL
      }
    )
  })

  output$metrics <- renderTable({
    result <- analysis()
    req(result)
    data.frame(
      Metric = c(
        "Model",
        "Calibration samples",
        "Test samples",
        "Components fitted",
        "Test RMSE",
        "Test R²"
      ),
      Value = c(
        result$model_type,
        length(result$train_indices),
        length(result$test_indices),
        result$ncomp,
        format(round(result$rmse, 3), nsmall = 3),
        format(round(result$r_squared, 3), nsmall = 3)
      ),
      check.names = FALSE
    )
  }, striped = TRUE, bordered = TRUE, spacing = "s")

  output$spectra <- renderPlot({
    result <- analysis()
    req(result)
    selected <- head(result$train_indices, 12)
    graphics::matplot(
      gasoline_data$wavelengths,
      t(gasoline_data$X[selected, , drop = FALSE]),
      type = "l",
      lty = 1,
      col = grDevices::adjustcolor("#246B8E", alpha.f = 0.45),
      xlab = "Wavelength (nm)",
      ylab = "Absorbance",
      main = "Calibration spectra"
    )
    graphics::grid()
  })

  output$cv <- renderPlot({
    result <- analysis()
    req(result)
    graphics::plot(
      result$cv$components,
      result$cv$rmsep,
      type = "b",
      pch = 16,
      col = "#246B8E",
      xlab = "Number of components",
      ylab = "RMSEP (LOO cross-validation)",
      main = paste(result$model_type, "cross-validation")
    )
    graphics::abline(v = result$ncomp, lty = 2, col = "#C4543D")
    graphics::grid()
  })

  output$predictions <- renderPlot({
    result <- analysis()
    req(result)
    observed <- result$predictions$observed
    predicted <- result$predictions$predicted
    graphics::plot(
      observed,
      predicted,
      pch = 19,
      col = "#246B8E",
      xlab = "Observed octane rating",
      ylab = "Predicted octane rating",
      main = "Predictions on the test set"
    )
    graphics::abline(0, 1, lty = 2, col = "#C4543D")
    graphics::grid()
  })
}

shinyApp(ui = ui, server = server)
