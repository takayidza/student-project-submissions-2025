using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using Microsoft.EntityFrameworkCore;

namespace CPRM2.Models;

[Table("products")]
public partial class Product
{
    [Key]
    [Column("product_id")]
    public int ProductId { get; set; }

    [Column("product_name")]
    [StringLength(100)]
    [Unicode(false)]
    public string ProductName { get; set; }

    [Column("description", TypeName = "text")]
    public string Description { get; set; }

    [Column("price")]
    public double? Price { get; set; }

    [Column("quantity")]
    public int? Quantity { get; set; }

    [Column("image_url")]
    [StringLength(255)]
    [Unicode(false)]
    public string ImageUrl { get; set; }

    [Column("is_active")]
    public bool? IsActive { get; set; }

    [Column("created_at", TypeName = "datetime")]
    public DateTime? CreatedAt { get; set; }

    [InverseProperty("Product")]
    public virtual ICollection<OrderItem> OrderItems { get; set; } = new List<OrderItem>();
}
