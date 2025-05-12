using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using Microsoft.EntityFrameworkCore;

namespace WaterQM.Models;

[Index("ParameterName", Name = "UQ__WaterPar__33CADFA1B07FB313", IsUnique = true)]
public partial class WaterParameter
{
    [Key]
    [Column("id")]
    public int Id { get; set; }

    [Column("parameter_name")]
    [StringLength(50)]
    public string ParameterName { get; set; } = null!;

    [InverseProperty("Parameter")]
    public virtual ICollection<SensorReading> SensorReadings { get; set; } = new List<SensorReading>();

    [InverseProperty("Parameter")]
    public virtual ICollection<Threshold> Thresholds { get; set; } = new List<Threshold>();
}
