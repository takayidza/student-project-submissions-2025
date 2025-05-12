am4core.ready(function() {
    am4core.useTheme(am4themes_animated);

    // Create chart
    var chart = am4core.create("weekly_wateruse_chart", am4charts.XYChart);
    chart.hiddenState.properties.opacity = 0; // Hide chart initially

    chart.colors.step = 2;
    chart.maskBullets = false;

    // Load data from Django API
    fetch("/apimonitor/weeklyusage/")
        .then(response => response.json())
        .then(data => {
            // Prepare data for chart
            chart.data = data.map(entry => ({
                timestamp: entry.timestamp,
                water_usage: Math.abs(entry.predicted_water_usage),  // show as positive
                water_level: entry.predicted_water_level
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
    valueAxis.title.text = "Water Usage";
    valueAxis.renderer.minGridDistance = 50;
    valueAxis.renderer.grid.template.disabled = true;

    // var usageAxis = chart.yAxes.push(new am4charts.ValueAxis());
    // usageAxis.title.text = 'Water Usage';
    // usageAxis.renderer.opposite = true;
    // usageAxis.syncWithAxis = valueAxis;
    // usageAxis.renderer.grid.template.disabled = true;

    // Water Usage Series
    var usageSeries = chart.series.push(new am4charts.ColumnSeries());
    usageSeries.dataFields.valueY = "water_usage";
    usageSeries.dataFields.categoryX = "timestamp";
    usageSeries.name = "Water Usage";
    usageSeries.stroke = am4core.color("#13afb2");
    usageSeries.columns.template.fillOpacity = 0.7;
    usageSeries.columns.template.propertyFields.strokeDasharray = 'dashLength';
    usageSeries.columns.template.propertyFields.fillOpacity = 'alpha';
    usageSeries.showOnInit = true;
    usageSeries.columns.template.tooltipText = "{name}: [bold]{valueY}[/]";
    usageSeries.columns.template.strokeWidth = 0; // optional: no border

    // Customize tooltip appearance
    usageSeries.tooltip.getFillFromObject = false;
    usageSeries.tooltip.background.fill = am4core.color('#13afb2').lighten(0.2);
    usageSeries.tooltip.background.fillOpacity = 0.5;
    usageSeries.tooltip.background.stroke = am4core.color('#13afb2');
    usageSeries.tooltip.label.fill = am4core.color('#000000');

    // Hover state
    var usageSeriesState = usageSeries.columns.template.states.create('hover');
    usageSeriesState.properties.fillOpacity = 0.9;

    
    
    // // Water Level Series
    // var levelSeries = chart.series.push(new am4charts.LineSeries());
    // levelSeries.dataFields.valueY = "water_level";
    // levelSeries.dataFields.categoryX = "timestamp";
    // levelSeries.name = "Water Level";
    // levelSeries.strokeWidth = 2;
    // levelSeries.propertyFields.strokeDasharray = 'dashLength';
    // levelSeries.showOnInit = true;
    // levelSeries.stroke = am4core.color("#4682B4");
    // levelSeries.strokeWidth = 2;
    // levelSeries.tooltipText = "{name}: [bold]{valueY}[/]";

    // // Customize tooltip appearance for seriesmemberCont
    // levelSeries.tooltip.getFillFromObject = false;
    // levelSeries.tooltip.background.fill = am4core.color('#4682B4').lighten(0.2); // Change tooltip background color
    // levelSeries.tooltip.background.fillOpacity = 0.5;
    // levelSeries.tooltip.background.stroke = am4core.color('#4682B4'); // Change tooltip border color
    // levelSeries.tooltip.label.fill = am4core.color('#000000'); // Change tooltip text color

    // levelSeries.strokeDasharray = '5, 5';

    // // Set tension for curved lines
    // levelSeries.tensionX = 1; // Adjust the tension as needed for the desired curve
    // levelSeries.tensionY = 1; // Adjust the tension as needed for the desired curve

    // var levelSeriesBullet = levelSeries.bullets.push(new am4charts.CircleBullet());
    // levelSeriesBullet.circle.fill = am4core.color('#fff');
    // levelSeriesBullet.circle.strokeWidth = 2;

    // var levelSeriesState = levelSeriesBullet.states.create('hover');
    // levelSeriesState.properties.scale = 1.2;

    // var levelSeriesLabel = levelSeries.bullets.push(new am4charts.LabelBullet());
    // levelSeriesLabel.label.horizontalCenter = 'left';
    // levelSeriesLabel.label.dx = 14;

    // Add legend and cursor
    chart.legend = new am4charts.Legend();
    chart.cursor = new am4charts.XYCursor();
    chart.cursor.behavior = "panX";
    chart.cursor.lineX.disabled = false;
    chart.cursor.lineY.disabled = true;

    chart.logo.disabled = true;
})
