using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using Microsoft.EntityFrameworkCore;

namespace CPRM2.Models;

[Table("order_items")]
public partial class OrderItem
{
    [Key]
    [Column("order_item_id")]
    public int OrderItemId { get; set; }

    [Column("order_id")]
    public int? OrderId { get; set; }

    [Column("product_id")]
    public int? ProductId { get; set; }

    [Column("quantity")]
    public int? Quantity { get; set; }

    [Column("unit_price")]
    public double? UnitPrice { get; set; }

    [ForeignKey("OrderId")]
    [InverseProperty("OrderItems")]
    public virtual Order Order { get; set; }

    [ForeignKey("ProductId")]
    [InverseProperty("OrderItems")]
    public virtual Product Product { get; set; }
}
