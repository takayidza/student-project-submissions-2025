am4core.ready(function() {
    am4core.useTheme(am4themes_animated);

    // Create chart
    var chart = am4core.create("weekly_humidity_chart", am4charts.XYChart);
    chart.hiddenState.properties.opacity = 0; // Hide chart initially

    chart.colors.step = 2;
    chart.maskBullets = false;

    // Load data from Django API
    fetch("/apimonitor/weatherforecast/")
        .then(response => response.json())
        .then(data => {
            // Prepare data for chart
            chart.data = data.daily.map(entry => ({
                timestamp: entry.timestamp,
                humidity: entry.humidity
            }));            
        });

    // Create category axis (X)
    var categoryAxis = chart.xAxes.push(new am4charts.CategoryAxis());
    categoryAxis.dataFields.category = "timestamp";
    categoryAxis.title.text = "Day of the week";
    categoryAxis.renderer.grid.template.location = 0;
    categoryAxis.renderer.minGridDistance = 50;
    categoryAxis.renderer.grid.template.disabled = true;
    categoryAxis.renderer.fullWidthTooltip = true;

    // Create value axis (Y)
    var valueAxis = chart.yAxes.push(new am4charts.ValueAxis());
    valueAxis.title.text = "Humidity %";
    valueAxis.renderer.minGridDistance = 50;
    valueAxis.renderer.grid.template.disabled = true;

    // Humidity Series
    var humiditySeries = chart.series.push(new am4charts.ColumnSeries());
    humiditySeries.dataFields.valueY = "humidity";
    humiditySeries.dataFields.categoryX = "timestamp";
    humiditySeries.name = "Humidity";
    humiditySeries.stroke = am4core.color("#004687");
    humiditySeries.columns.template.fill = am4core.color("#004687");
    humiditySeries.columns.template.fillOpacity = 0.7;
    humiditySeries.columns.template.propertyFields.strokeDasharray = 'dashLength';
    humiditySeries.columns.template.propertyFields.fillOpacity = 'alpha';
    humiditySeries.showOnInit = true;
    humiditySeries.columns.template.tooltipText = "{name}: [bold]{valueY}[/]";
    humiditySeries.columns.template.strokeWidth = 0; // optional: no border

    // Customize tooltip appearance
    humiditySeries.tooltip.getFillFromObject = false;
    humiditySeries.tooltip.background.fill = am4core.color('#004687').lighten(0.2);
    humiditySeries.tooltip.background.fillOpacity = 0.5;
    humiditySeries.tooltip.background.stroke = am4core.color('#004687');
    humiditySeries.tooltip.label.fill = am4core.color('#000000');

    // Hover state
    var humiditySeriesState = humiditySeries.columns.template.states.create('hover');
    humiditySeriesState.properties.fillOpacity = 0.9;

    

    // Add legend and cursor
    chart.legend = new am4charts.Legend();
    chart.cursor = new am4charts.XYCursor();
    chart.cursor.behavior = "panX";
    chart.cursor.lineX.disabled = false;
    chart.cursor.lineY.disabled = true;

    chart.logo.disabled = true;
})
