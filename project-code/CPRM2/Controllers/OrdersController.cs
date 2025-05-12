using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.Rendering;
using Microsoft.EntityFrameworkCore;
using CPRM2.Data;
using CPRM2.Models;
using Microsoft.AspNetCore.Authorization;
using System.Security.Claims;
using System.Text.Json;
using CPRM2.Extensions;
using Webdev.Payments;
using NuGet.Protocol;

namespace CPRM2.Controllers
{
    [Authorize]
    public class OrdersController : Controller
    {
        private readonly CprmDbContext _context;
        private const string CartSessionKey = "ShoppingCart";
        private Paynow paynow = new Paynow("20785", "d678ecdd-6800-48e2-ba50-90edcef6e3a2");
        public OrdersController(CprmDbContext context)
        {
            _context = context;
        }

        // GET: Orders
        [Authorize(Roles = "Admin")]
        public async Task<IActionResult> Client()
        {

            var orders = await _context.Orders
                .Include(o => o.OrderItems)
                    .ThenInclude(oi => oi.Product)

                .OrderByDescending(o => o.OrderDate)
                .ToListAsync();

            return View(orders);
        }
        // GET: Orders
        public async Task<IActionResult> Index()
        {
            var userId = User.FindFirstValue(ClaimTypes.NameIdentifier);
            var orders = await _context.Orders
                .Include(o => o.OrderItems)
                    .ThenInclude(oi => oi.Product)
                .Where(o => o.UserId == userId)
                .OrderByDescending(o => o.OrderDate)
                .ToListAsync();

            return View(orders);
        }

        // GET: Orders/Details/5
        public async Task<IActionResult> Details(int? id)
        {
            if (id == null)
            {
                return NotFound();
            }



            var userId = User.FindFirstValue(ClaimTypes.NameIdentifier);
            var order = await _context.Orders
                .Include(o => o.OrderItems)
                    .ThenInclude(oi => oi.Product)
                .FirstOrDefaultAsync(m => m.OrderId == id && m.UserId == userId);

            var result = await paynow.PollTransactionAsync(order.PaymentMethod);

            if (result.WasPaid)
            {
                order.PaymentStatus = "Paid";
                order.OrderStatus = "Processing";
                //deduct the products from the inventory
                string sql = "";
                foreach (var item in order.OrderItems)
                {
                    sql += $"UPDATE Products SET Quantity = Quantity - {item.Quantity} WHERE Product_Id = {item.ProductId};";
                }
                await _context.Database.ExecuteSqlRawAsync(sql);
                _context.Update(order);
                await _context.SaveChangesAsync();
            }
            if (order == null)
            {
                return NotFound();
            }

            return View(order);
        }

        // GET: Orders/Cart
        public IActionResult Cart()
        {
            var cart = GetCart();
            return View(cart);
        }

        // POST: Orders/AddToCart
        [HttpPost]
        public async Task<IActionResult> AddToCart(int productId, int quantity)
        {
            var product = await _context.Products.FindAsync(productId);
            if (product == null || !product.IsActive == true)
            {
                return Json(new { success = false, message = "Product not found or not available" });
            }

            var cart = GetCart();
            var cartItem = cart.FirstOrDefault(i => i.ProductId == productId);

            if (cartItem != null)
            {
                cartItem.Quantity += quantity;
            }
            else
            {
                cart.Add(new OrderItem
                {
                    ProductId = productId,
                    Quantity = quantity,
                    UnitPrice = product.Price ?? 0
                });
            }

            SaveCart(cart);
            return Json(new { success = true, cartCount = cart.Sum(i => i.Quantity) });
        }

        // POST: Orders/UpdateCart
        [HttpPost]
        public IActionResult UpdateCart(int productId, int quantity)
        {
            var cart = GetCart();
            var cartItem = cart.FirstOrDefault(i => i.ProductId == productId);

            if (cartItem != null)
            {
                if (quantity <= 0)
                {
                    cart.Remove(cartItem);
                }
                else
                {
                    cartItem.Quantity = quantity;
                }
                SaveCart(cart);
            }

            return Json(new { success = true, cartCount = cart.Sum(i => i.Quantity) });
        }

        // POST: Orders/RemoveFromCart
        [HttpPost]
        public IActionResult RemoveFromCart(int productId)
        {
            var cart = GetCart();
            var cartItem = cart.FirstOrDefault(i => i.ProductId == productId);

            if (cartItem != null)
            {
                cart.Remove(cartItem);
                SaveCart(cart);
            }

            return Json(new { success = true, cartCount = cart.Sum(i => i.Quantity) });
        }

        // GET: Orders/Checkout
        public async Task<IActionResult> Checkout()
        {
            var cart = GetCart();
            if (!cart.Any())
            {
                return RedirectToAction(nameof(Cart));
            }

            // Load product details for cart items
            foreach (var item in cart)
            {
                var product = await _context.Products.FindAsync(item.ProductId);
                if (product != null)
                {
                    item.Product = product;
                }
            }

            return View(new Order()
            {
                OrderDate = DateTime.Now,
                OrderStatus = "Pending",
                PaymentMethod = "PayNow",
                PaymentStatus = "Pending",
                TotalAmount = cart.Sum(i => i.UnitPrice * i.Quantity),
                OrderItems = cart
            });
        }

        // POST: Orders/PlaceOrder
        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> PlaceOrder(string paymentMethod)
        {
            var cart = GetCart();
            if (!cart.Any())
            {
                return RedirectToAction(nameof(Cart));
            }

            var userId = User.FindFirstValue(ClaimTypes.NameIdentifier);
            var totalAmount = cart.Sum(i => i.UnitPrice * i.Quantity);



            List<OrderItem> orderItems = new List<OrderItem>();
            // Add order items
            foreach (var item in cart)
            {
                var orderItem = new OrderItem
                {

                    ProductId = item.ProductId,
                    Quantity = item.Quantity,
                    UnitPrice = item.UnitPrice
                };
                orderItems.Add(orderItem);

            }
            // Create the order
            var order = new Order
            {
                UserId = userId,
                OrderDate = DateTime.UtcNow,
                TotalAmount = totalAmount,
                PaymentMethod = paymentMethod,
                PaymentStatus = "Pending",
                OrderStatus = "Pending",
                OrderItems = orderItems
            };

            // Save the order to the database
            _context.Add(order);

            await _context.SaveChangesAsync();
            return await RetryPayment(order.OrderId);
            // Clear the cart



        }
        public async Task<IActionResult> RetryPayment(int id)
        {

            var order = await _context.Orders.AsNoTracking()
                    .Include(d => d.OrderItems)
                .AsSplitQuery()
                .FirstOrDefaultAsync(d => d.OrderId == id);


            var request = HttpContext.Request;
            var baseUrl = $"{request.Scheme}://{request.Host}";

            // Now use this for your Paynow URLs
            paynow.ResultUrl = $"{baseUrl}/Orders/Details/{order.OrderId}";
            paynow.ReturnUrl = $"{baseUrl}/Orders/Details/{order.OrderId}";

            // The return url can be set at later stages. You might want to do this if you want to pass data to the return url (like the reference of the transaction)

            // Create a new payment 
            var payment = paynow.CreatePayment("Order ID:" + "#000-" + order.OrderId);


            // Add items to the payment
            foreach (var item in order.OrderItems)
            {
                payment.Add(item.ProductId.ToString(), (decimal)item.UnitPrice.Value);
            }
            // Send payment to paynow
            var response = paynow.Send(payment);


            // Check if payment was sent without error
            if (response.Success())
            {
                // Get the url to redirect the user to so they can make payment
                var link = response.RedirectLink();


                // Get the poll url of the transaction

                var pollUrl = response.PollUrl();
                order.PaymentMethod = pollUrl;

                Console.WriteLine("----------------------------" + pollUrl);
                await _context.Database.ExecuteSqlRawAsync($"UPDATE Orders SET Payment_Method = '{pollUrl}' WHERE Order_Id = {order.OrderId}");

                ClearCart();
                return Redirect(link);

            }
            else
            {
                return Ok(response);
            }
            // TODO: Implement PayNow integration
            return RedirectToAction(nameof(PaymentSuccess), new { orderId = order.OrderId });

        }

        // GET: Orders/PaymentSuccess
        public async Task<IActionResult> PaymentSuccess(int orderId)
        {
            var userId = User.FindFirstValue(ClaimTypes.NameIdentifier);
            var order = await _context.Orders
                .Include(o => o.OrderItems)
                    .ThenInclude(oi => oi.Product)
                .FirstOrDefaultAsync(o => o.OrderId == orderId && o.UserId == userId);

            if (order == null)
            {
                return NotFound();
            }

            // Update order status
            order.PaymentStatus = "Paid";
            order.OrderStatus = "Processing";
            await _context.SaveChangesAsync();

            return View(order);
        }

        // GET: Orders/GetCartCount
        [HttpGet]
        public IActionResult GetCartCount()
        {
            var cart = GetCart();
            return Json(cart.Sum(i => i.Quantity));
        }

        private List<OrderItem> GetCart()
        {
            return HttpContext.Session.GetObject<List<OrderItem>>(CartSessionKey) ?? new List<OrderItem>();
        }

        private void SaveCart(List<OrderItem> cart)
        {
            HttpContext.Session.SetObject(CartSessionKey, cart);
        }

        [Authorize(Roles = "Admin")]
        public async Task<IActionResult> DeleteAllOrdersWithNoItems()
        {
            var orders = await _context.Orders.Include(o => o.OrderItems)
            .AsNoTracking()
            .Where(o => o.OrderItems.Count == 0).ToListAsync();
            _context.Orders.RemoveRange(orders);
            await _context.SaveChangesAsync();
            return RedirectToAction(nameof(Client));
        }
        [Authorize(Roles = "Admin")]
        public async Task<IActionResult> DeleteAllOrders()
        {
            var orders = await _context.Orders.Include(o => o.OrderItems)
            .AsNoTracking()
           .ToListAsync();
            _context.Orders.RemoveRange(orders);
            await _context.SaveChangesAsync();
            return RedirectToAction(nameof(Client));
        }

        [Authorize(Roles = "Admin")]
        public async Task<IActionResult> Dispatch(int id)
        {
            var order = await _context.Orders.FindAsync(id);
            order.OrderStatus = "Dispatched";

            await _context.SaveChangesAsync();
            return RedirectToAction(nameof(Client));
        }
        private void ClearCart()
        {
            HttpContext.Session.Remove(CartSessionKey);
        }
    }
}
