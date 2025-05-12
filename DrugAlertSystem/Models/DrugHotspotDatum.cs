using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using Microsoft.EntityFrameworkCore;

namespace DrugAlertSystem.Models;

public partial class DrugHotspotDatum
{
    [Key]
    public int Id { get; set; }

    [Required]
    [StringLength(255)]
    public string Location { get; set; }

    public bool? PeopleLoitering { get; set; }

    public bool? DrugWrappersFound { get; set; }

    public bool? StrongSmell { get; set; }

    public bool? LoudNoiseOrMusic { get; set; }

    public bool? ShoeHangingOnWire { get; set; }

    public bool? PeopleInAndOut { get; set; }

    public Guid ReportId { get; set; }

    [Column("ishotspot")]
    public bool? Ishotspot { get; set; }

    [Column("probability")]
    public double? Probability { get; set; }

    [Column("score")]
    public double? Score { get; set; }

    [ForeignKey("ReportId")]
    [InverseProperty("DrugHotspotData")]
    public virtual Report Report { get; set; }
}
