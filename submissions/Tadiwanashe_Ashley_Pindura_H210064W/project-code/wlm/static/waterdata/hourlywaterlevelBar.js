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
  
        var chart = am4core.create("hourlywaterlevelBar", am4charts.XYChart);
        chart.hiddenState.properties.opacity = 0;
        chart.colors.step = 2;
        chart.maskBullets = false;
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
  
        // Create Column Series (was LineSeries)
        var series = chart.series.push(new am4charts.ColumnSeries());
        series.dataFields.valueY = "level";
        series.dataFields.categoryX = "timestamp";
        series.yAxis = valueAxis;
        series.name = "Water Level";
        series.columns.template.strokeWidth = 0;
        series.columns.template.fill = am4core.color("#4682B4"); // SteelBlue
        series.tooltipText = "Water Level: {valueY}";
  
        // Customize tooltip
        series.tooltip.getFillFromObject = false;
        series.tooltip.background.fill = am4core.color("#4682B4").lighten(0.2);
        series.tooltip.background.fillOpacity = 0.5;
        series.tooltip.background.stroke = am4core.color("#4682B4");
        series.tooltip.label.fill = am4core.color("#000000");
  
        // Add cursor
        chart.cursor = new am4charts.XYCursor();
        chart.cursor.fullWidthLineX = true;
        chart.cursor.xAxis = categoryAxis;
        chart.cursor.lineX.strokeOpacity = 0;
        chart.cursor.lineX.fill = am4core.color("#000");
        chart.cursor.lineX.fillOpacity = 0.1;
  
        // Optional: chart legend, scrollbar
        // chart.legend = new am4charts.Legend();
        // chart.scrollbarX = new am4core.Scrollbar();
  
        chart.logo.disabled = true;
      })
      .catch((error) => {
        console.error("Error fetching data:", error);
      });
  });
  