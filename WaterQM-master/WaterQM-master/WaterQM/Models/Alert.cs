using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using Microsoft.EntityFrameworkCore;

namespace WaterQM.Models;

public partial class Alert
{
    [Key]
    [Column("id")]
    public int Id { get; set; }

    [Column("sensor_id")]
    public int SensorId { get; set; }

    [Column("user_id")]
    [StringLength(450)]
    public string UserId { get; set; } = null!;

    [Column("alert_message")]
    [StringLength(255)]
    public string AlertMessage { get; set; } = null!;

    [Column("alert_time", TypeName = "datetime")]
    public DateTime AlertTime { get; set; }

    [InverseProperty("Alert")]
    public virtual ICollection<Notification> Notifications { get; set; } = new List<Notification>();

    [ForeignKey("SensorId")]
    [InverseProperty("Alerts")]
    public virtual Sensor Sensor { get; set; } = null!;

    [ForeignKey("UserId")]
    [InverseProperty("Alerts")]
    public virtual User User { get; set; } = null!;
}
