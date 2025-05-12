from django.db import models

# Create your models here.
from django.db import models

class SensorData(models.Model):
    temperature = models.FloatField()
    humidity = models.FloatField()
    timestamp = models.DateTimeField()

    def __str__(self):
        return f"Temp: {self.temperature}°C, Humidity: {self.humidity}%"

class WaterLevel(models.Model):
    level = models.FloatField()
    timestamp = models.DateTimeField()
    sensor_data = models.ForeignKey(SensorData, on_delete=models.CASCADE, related_name='water_levels')

    def __str__(self):
        return f"Level: {self.level}% (Sensor: {self.sensor_data})"
