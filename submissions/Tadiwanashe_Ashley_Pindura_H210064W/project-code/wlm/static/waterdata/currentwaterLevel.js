document.addEventListener("DOMContentLoaded", function () {
    am5.ready(function() {
        var root = am5.Root.new("chartdiv");
        root.setThemes([am5themes_Animated.new(root)]);

        var chart = root.container.children.push(
            am5radar.RadarChart.new(root, {
                panX: false,
                panY: false,
                startAngle: 180,
                endAngle: 360
            })
        );

        chart.getNumberFormatter().set("numberFormat", "#'%'");

        var axisRenderer = am5radar.AxisRendererCircular.new(root, {
            innerRadius: -40
        });

        axisRenderer.grid.template.setAll({
            stroke: root.interfaceColors.get("background"),
            visible: true,
            strokeOpacity: 0.8
        });

        var xAxis = chart.xAxes.push(
            am5xy.ValueAxis.new(root, {
                maxDeviation: 0,
                min: 0,
                max: 100,
                strictMinMax: true,
                renderer: axisRenderer
            })
        );

        var axisDataItem = xAxis.makeDataItem({});
        var clockHand = am5radar.ClockHand.new(root, {
            pinRadius: 50,
            radius: am5.percent(100),
            innerRadius: 50,
            bottomWidth: 0,
            topWidth: 0
        });

        clockHand.pin.setAll({
            fillOpacity: 0,
            strokeOpacity: 0.5,
            stroke: am5.color(0x000000),
            strokeWidth: 1,
            strokeDasharray: [2, 2]
        });

        clockHand.hand.setAll({
            fillOpacity: 0,
            strokeOpacity: 0.5,
            stroke: am5.color(0x000000),
            strokeWidth: 0.5
        });

        var bullet = axisDataItem.set(
            "bullet",
            am5xy.AxisBullet.new(root, { sprite: clockHand })
        );

        xAxis.createAxisRange(axisDataItem);

        var label = chart.radarContainer.children.push(
            am5.Label.new(root, {
                centerX: am5.percent(50),
                textAlign: "center",
                centerY: am5.percent(50),
                fontSize: "1.5em"
            })
        );

        axisDataItem.set("value", 50);
        bullet.get("sprite").on("rotation", function () {
            var value = axisDataItem.get("value");
            label.set("text", Math.round(value).toString() + "%");
        });

        var colorSet = am5.ColorSet.new(root, {});

        var axisRange0 = xAxis.createAxisRange(
            xAxis.makeDataItem({ above: true, value: 0, endValue: 50 })
        );
        axisRange0.get("axisFill").setAll({
            visible: true,
            fill: colorSet.getIndex(0)
        });

        var axisRange1 = xAxis.createAxisRange(
            xAxis.makeDataItem({ above: true, value: 50, endValue: 100 })
        );
        axisRange1.get("axisFill").setAll({
            visible: true,
            fill: colorSet.getIndex(4)
        });

        function updateGauge() {
            fetch("/api/get-latest-water-level/")
            .then(response => response.json())
            .then(data => {
                if (data.water_level !== undefined) {
                    axisDataItem.animate({
                        key: "value",
                        to: data.water_level,
                        duration: 500,
                        easing: am5.ease.out(am5.ease.cubic)
                    });

                    axisRange0.animate({
                        key: "endValue",
                        to: data.water_level,
                        duration: 500,
                        easing: am5.ease.out(am5.ease.cubic)
                    });

                    axisRange1.animate({
                        key: "value",
                        to: data.water_level,
                        duration: 500,
                        easing: am5.ease.out(am5.ease.cubic)
                    });
                }
            })
            .catch(error => console.log("Error fetching data:", error));
        }

        setInterval(updateGauge, 2000);
    }); 
});
