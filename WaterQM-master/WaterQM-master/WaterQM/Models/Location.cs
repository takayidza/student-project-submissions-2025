using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using Microsoft.EntityFrameworkCore;

namespace WaterQM.Models;

[Index("LocationName", Name = "UQ__Location__F809DCA0300A6811", IsUnique = true)]
public partial class Location
{
    [Key]
    [Column("id")]
    public int Id { get; set; }

    [Column("location_name")]
    [StringLength(100)]
    public string LocationName { get; set; } = null!;

    [Column("latitude", TypeName = "decimal(9, 6)")]
    public decimal Latitude { get; set; }

    [Column("longitude", TypeName = "decimal(9, 6)")]
    public decimal Longitude { get; set; }

    [InverseProperty("Location")]
    public virtual ICollection<Sensor> Sensors { get; set; } = new List<Sensor>();
}
