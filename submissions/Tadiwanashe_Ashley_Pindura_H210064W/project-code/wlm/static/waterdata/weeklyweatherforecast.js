am4core.ready(function() {
    am4core.useTheme(am4themes_animated);

    // Create chart
    var chart = am4core.create("weekly_weatherforecast_chart", am4charts.XYChart);
    chart.hiddenState.properties.opacity = 0; // Hide chart initially

    chart.colors.step = 2;
    chart.maskBullets = false;

    // Load data from Django API
    fetch("/apimonitor/weatherforecast/")
        .then(response => response.json())
        .then(data => {
            // Prepare data for chart
            chart.data = data.daily.map(entry => ({
                timestamp: entry.timestamp, // e.g., "Monday"
                avg_temperature: entry.temperature_avg,
                temperature_min: entry.temperature_min,
                temperature_max: entry.temperature_max,
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
    valueAxis.title.text = "Temperature";
    valueAxis.renderer.minGridDistance = 50;
    valueAxis.renderer.grid.template.disabled = true;

    // var usageAxis = chart.yAxes.push(new am4charts.ValueAxis());
    // usageAxis.title.text = 'Water Usage';
    // usageAxis.renderer.opposite = true;
    // usageAxis.syncWithAxis = valueAxis;
    // usageAxis.renderer.grid.template.disabled = true;

    // Water Usage Series
    var avgtempSeries = chart.series.push(new am4charts.ColumnSeries());
    avgtempSeries.dataFields.valueY = "avg_temperature";
    avgtempSeries.dataFields.categoryX = "timestamp";
    avgtempSeries.name = "Avg Temperature";
    avgtempSeries.columns.template.fill = am4core.color("#F4BB44");
    avgtempSeries.stroke = am4core.color("#F4BB44");
    avgtempSeries.columns.template.fillOpacity = 0.7;
    avgtempSeries.columns.template.propertyFields.strokeDasharray = 'dashLength';
    avgtempSeries.columns.template.propertyFields.fillOpacity = 'alpha';
    avgtempSeries.showOnInit = true;
    avgtempSeries.columns.template.tooltipText = "{name}: [bold]{valueY}[/]\n";
    avgtempSeries.columns.template.strokeWidth = 0; // optional: no border

    // Customize tooltip appearance
    avgtempSeries.tooltip.getFillFromObject = false;
    avgtempSeries.tooltip.background.fill = am4core.color('#F4BB44').lighten(0.2);
    avgtempSeries.tooltip.background.fillOpacity = 0.5;
    avgtempSeries.tooltip.background.stroke = am4core.color('#F4BB44');
    avgtempSeries.tooltip.label.fill = am4core.color('#000000');
    avgtempSeries.tooltip.pointerOrientation = "right";

    // Hover state
    var avgtempSeriesState = avgtempSeries.columns.template.states.create('hover');
    avgtempSeriesState.properties.fillOpacity = 0.9;

    
    
    // // Water Level Series
    var maxtempSeries = chart.series.push(new am4charts.LineSeries());
    maxtempSeries.dataFields.valueY = "temperature_max";
    maxtempSeries.dataFields.categoryX = "timestamp";
    maxtempSeries.name = "Max Temperature";
    maxtempSeries.strokeWidth = 2;
    maxtempSeries.propertyFields.strokeDasharray = 'dashLength';
    maxtempSeries.showOnInit = true;
    maxtempSeries.stroke = am4core.color("#fe7383");
    maxtempSeries.strokeWidth = 2;
    maxtempSeries.tooltipText = "{name}: [bold]{valueY}[/]\n";

    // // Customize tooltip appearance for seriesmemberCont
    maxtempSeries.tooltip.getFillFromObject = false;
    maxtempSeries.tooltip.background.fill = am4core.color('#fe7383').lighten(0.2); // Change tooltip background color
    maxtempSeries.tooltip.background.fillOpacity = 0.5;
    maxtempSeries.tooltip.background.stroke = am4core.color('#fe7383'); // Change tooltip border color
    maxtempSeries.tooltip.label.fill = am4core.color('#000000'); // Change tooltip text color
    maxtempSeries.tooltip.pointerOrientation = "down";

    maxtempSeries.strokeDasharray = '5, 5';

    // // Set tension for curved lines
    maxtempSeries.tensionX = 0.6; // Adjust the tension as needed for the desired curve
    maxtempSeries.tensionY = 1; // Adjust the tension as needed for the desired curve
    
    var maxtempSeriesBullet = maxtempSeries.bullets.push(new am4charts.CircleBullet());
    maxtempSeriesBullet.circle.fill = am4core.color('#fff');
    maxtempSeriesBullet.circle.strokeWidth = 2;

    var maxtempSeriesState = maxtempSeriesBullet.states.create('hover');
    maxtempSeriesState.properties.scale = 1.2;

    var maxtempSeriesLabel = maxtempSeries.bullets.push(new am4charts.LabelBullet());
    maxtempSeriesLabel.label.horizontalCenter = 'left';
    maxtempSeriesLabel.label.dx = 14;

    // Create 'Member Count' series
    var mintempSeries = chart.series.push(new am4charts.LineSeries());
    mintempSeries.dataFields.valueY = 'temperature_min';
    mintempSeries.dataFields.categoryX = 'timestamp';
    // mintempSeries.yAxis = memberAxis;
    mintempSeries.name = 'Min Temperature';
    mintempSeries.strokeWidth = 2;
    mintempSeries.propertyFields.strokeDasharray = 'dashLength';
    mintempSeries.tooltipText = '{name}: [bold]{valueY}[/]';
    mintempSeries.showOnInit = true;
    mintempSeries.stroke = am4core.color('#005A9C');

    // Customize tooltip appearance for seriesmemberCont
    mintempSeries.tooltip.getFillFromObject = false;
    mintempSeries.tooltip.background.fill = am4core.color('#005A9C').lighten(0.2); // Change tooltip background color
    mintempSeries.tooltip.background.fillOpacity = 0.5;
    mintempSeries.tooltip.background.stroke = am4core.color('#005A9C'); // Change tooltip border color
    mintempSeries.tooltip.label.fill = am4core.color('#000000'); // Change tooltip text color
    mintempSeries.tooltip.pointerOrientation = "left";

    // Configure broken line

    mintempSeries.tensionX = 1; // Adjust the tension as needed for the desired curve
    mintempSeries.tensionY = 1; // Adjust the tension as needed for the desired curve

    var mintempSeriesBullet = mintempSeries.bullets.push(new am4charts.CircleBullet());
    mintempSeriesBullet.circle.fill = am4core.color('#005A9C');
    mintempSeriesBullet.circle.strokeWidth = 2;

    var mintempSeriesState = mintempSeriesBullet.states.create('hover');
    mintempSeriesState.properties.scale = 1.2;

    var mintempSeriesLabel = mintempSeries.bullets.push(new am4charts.LabelBullet());
    mintempSeriesLabel.label.horizontalCenter = 'left';
    mintempSeriesLabel.label.dx = 14;

    // Add cursor
    chart.legend = new am4charts.Legend();
    
    // Add chart cursor
    chart.cursor = new am4charts.XYCursor();
    chart.cursor.fullWidthLineX = true;
    chart.cursor.xAxis = categoryAxis;
    chart.cursor.lineX.strokeOpacity = 0;
    chart.cursor.lineX.fill = am4core.color('#000');
    chart.cursor.lineX.fillOpacity = 0.1;
    chart.cursor.behavior = "none";  // disables zoom/pan/snap
    chart.cursor.snapToSeries = undefined; // disables snapping tooltips across series
    

    chart.logo.disabled = true;
})
