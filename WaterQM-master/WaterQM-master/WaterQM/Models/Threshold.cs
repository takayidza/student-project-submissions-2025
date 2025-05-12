using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using Microsoft.EntityFrameworkCore;

namespace WaterQM.Models;

public partial class Threshold
{
    [Key]
    [Column("id")]
    public int Id { get; set; }

    [Column("parameter_id")]
    public int ParameterId { get; set; }

    [Column("min_value")]
    public double MinValue { get; set; }

    [Column("max_value")]
    public double MaxValue { get; set; }

    [ForeignKey("ParameterId")]
    [InverseProperty("Thresholds")]
    public virtual WaterParameter Parameter { get; set; } = null!;
}
