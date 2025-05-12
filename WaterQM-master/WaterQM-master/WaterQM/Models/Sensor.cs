using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using Microsoft.EntityFrameworkCore;

namespace WaterQM.Models;

[Index("SensorName", Name = "UQ__Sensors__96382DC19B45A9A6", IsUnique = true)]
public partial class Sensor
{
    [Key]
    [Column("id")]
    public int Id { get; set; }

    [Column("sensor_name")]
    [StringLength(100)]
    public string SensorName { get; set; } = null!;

    [Column("sensor_type")]
    [StringLength(50)]
    public string SensorType { get; set; } = null!;

    [Column("location_id")]
    public int LocationId { get; set; }

    [InverseProperty("Sensor")]
    public virtual ICollection<Alert> Alerts { get; set; } = new List<Alert>();

    [ForeignKey("LocationId")]
    [InverseProperty("Sensors")]
    public virtual Location Location { get; set; } = null!;

    [InverseProperty("Sensor")]
    public virtual ICollection<SensorReading> SensorReadings { get; set; } = new List<SensorReading>();
}
