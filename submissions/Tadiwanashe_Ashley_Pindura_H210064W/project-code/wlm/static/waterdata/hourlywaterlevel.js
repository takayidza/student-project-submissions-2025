am4core.ready(function () {
    // Use animated theme
    am4core.useTheme(am4themes_animated);
  
    // Fetch the data from the new API endpoint
    fetch(`/api/hourly_water_level`)
      .then((response) => response.json())
      .then((data) => {
        if (data.error) {
          console.error(data.error);
          return;
        }
  
        var chart = am4core.create("hourlywaterlevel", am4charts.XYChart);
  
        chart.hiddenState.properties.opacity = 0; // Hide chart initially
  
        chart.colors.step = 2;
        chart.maskBullets = false;
  
        // Use the fetched data for the chart
        chart.data = data.chart_data;
  
        // Create axes
        var categoryAxis = chart.xAxes.push(new am4charts.CategoryAxis());
        categoryAxis.dataFields.category = "timestamp";
        categoryAxis.renderer.grid.template.location = 0;
        categoryAxis.renderer.minGridDistance = 50;
        categoryAxis.renderer.grid.template.disabled = true;
        categoryAxis.renderer.fullWidthTooltip = true;
  
        var valueAxis = chart.yAxes.push(new am4charts.ValueAxis());
        valueAxis.renderer.minGridDistance = 50;
        valueAxis.title.text = "Water Level";
        valueAxis.renderer.grid.template.disabled = true;
  
  
        
  
        // Create 'Member Count' series
        var seriesExpenses = chart.series.push(new am4charts.LineSeries());
        seriesExpenses.dataFields.valueY = "level";
        seriesExpenses.dataFields.categoryX = "timestamp";
        seriesExpenses.yAxis = valueAxis;
        seriesExpenses.name = "Water Level";
        seriesExpenses.strokeWidth = 2;
        seriesExpenses.propertyFields.strokeDasharray = "dashLength";
        seriesExpenses.tooltipText = "Water Level: \n{valueY}";
        seriesExpenses.showOnInit = true;
        seriesExpenses.stroke = am4core.color("#4682B4");
  
        // Customize tooltip appearance for seriesmemberCont
        seriesExpenses.tooltip.getFillFromObject = false;
        seriesExpenses.tooltip.background.fill = am4core
          .color("#4682B4")
          .lighten(0.2); // Change tooltip background color
        seriesExpenses.tooltip.background.fillOpacity = 0.5;
        seriesExpenses.tooltip.background.stroke = am4core.color("#4682B4"); // Change tooltip border color
        seriesExpenses.tooltip.label.fill = am4core.color("#000000"); // Change tooltip text color
  
        // Configure broken line
        //seriesExpenses.strokeDasharray = "5, 5";
  
        seriesExpenses.tensionX = 0.6; // Adjust the tension as needed for the desired curve
        seriesExpenses.tensionY = 1; // Adjust the tension as needed for the desired curve
  
        var ExpensesBullet = seriesExpenses.bullets.push(
          new am4charts.CircleBullet()
        );
        ExpensesBullet.circle.fill = am4core.color("#fff");
        ExpensesBullet.circle.strokeWidth = 2;
  
        var ExpensesState = ExpensesBullet.states.create("hover");
        ExpensesState.properties.scale = 1.2;
  
        var ExpensesLabel = seriesExpenses.bullets.push(
          new am4charts.LabelBullet()
        );
        ExpensesLabel.label.horizontalCenter = "left";
        ExpensesLabel.label.dx = 14;
  
        
  
        // Add a legend
        // chart.legend = new am4charts.Legend();
  
        // Add cursor
        chart.cursor = new am4charts.XYCursor();
        chart.cursor.fullWidthLineX = true;
        chart.cursor.xAxis = categoryAxis;
        chart.cursor.lineX.strokeOpacity = 0;
        chart.cursor.lineX.fill = am4core.color("#000");
        chart.cursor.lineX.fillOpacity = 0.1;
  
        // Add scrollbar
        //chart.scrollbarX = new am4core.Scrollbar();
  
        chart.logo.disabled = true;
      })
      .catch((error) => {
        console.error("Error fetching data:", error);
      });
  });