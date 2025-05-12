using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using Microsoft.EntityFrameworkCore;

namespace WaterQM.Models;

public partial class SensorReading
{
    [Key]
    [Column("id")]
    public int Id { get; set; }

    [Column("sensor_id")]
    public int SensorId { get; set; }

    [Column("parameter_id")]
    public int ParameterId { get; set; }

    [Column("reading_value")]
    public double ReadingValue { get; set; }

    [Column("reading_time", TypeName = "datetime")]
    public DateTime ReadingTime { get; set; }

    [ForeignKey("ParameterId")]
    [InverseProperty("SensorReadings")]
    public virtual WaterParameter Parameter { get; set; } = null!;

    [ForeignKey("SensorId")]
    [InverseProperty("SensorReadings")]
    public virtual Sensor Sensor { get; set; } = null!;
}
