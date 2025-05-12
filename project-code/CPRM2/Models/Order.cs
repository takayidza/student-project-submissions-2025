using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using Microsoft.EntityFrameworkCore;

namespace CPRM2.Models;

[Table("orders")]
public partial class Order
{
    [Key]
    [Column("order_id")]
    public int OrderId { get; set; }

    [Column("user_id")]
    [StringLength(450)]
    public string UserId { get; set; }

    [Column("order_date", TypeName = "datetime")]
    public DateTime? OrderDate { get; set; }

    [Column("total_amount")]
    public double? TotalAmount { get; set; }

    [Column("payment_method")]
  
    [Unicode(false)]
    public string PaymentMethod { get; set; }

    [Column("payment_status")]
    [StringLength(50)]
    [Unicode(false)]
    public string PaymentStatus { get; set; }

    [Column("order_status")]
    [StringLength(50)]
    [Unicode(false)]
    public string OrderStatus { get; set; }

    [InverseProperty("Order")]
    public virtual ICollection<OrderItem> OrderItems { get; set; } = new List<OrderItem>();

    [ForeignKey("UserId")]
    [InverseProperty("Orders")]
    public virtual User User { get; set; }
}
