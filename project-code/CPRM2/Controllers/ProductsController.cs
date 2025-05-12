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

namespace CPRM2.Controllers
{
    public class ProductsController : Controller
    {
        private readonly CprmDbContext _context;

        public ProductsController(CprmDbContext context)
        {
            _context = context;
        }

        // GET: Products
        public async Task<IActionResult> Admin()
        {
            return View(await _context.Products.ToListAsync());
        }
        // GET: Products
        public async Task<IActionResult> Index()
        {
            return View(await _context.Products.ToListAsync());
        }

        // GET: Products/Details/5
        public async Task<IActionResult> Details(int? id)
        {
            if (id == null)
            {
                return NotFound();
            }

            var product = await _context.Products
                .FirstOrDefaultAsync(m => m.ProductId == id);
            if (product == null)
            {
                return NotFound();
            }

            return View(product);
        }

        // GET: Products/Create
        public IActionResult Create()
        {
            return View();
        }

        // POST: Products/Create
        // To protect from overposting attacks, enable the specific properties you want to bind to.
        // For more details, see http://go.microsoft.com/fwlink/?LinkId=317598.
        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> Create( Product product)
        {
            if (ModelState.IsValid)
            {
                _context.Add(product);
                await _context.SaveChangesAsync();
                return RedirectToAction(nameof(Index));
            }
            return View(product);
        }

        // GET: Products/Edit/5
        public async Task<IActionResult> Edit(int? id)
        {
            if (id == null)
            {
                return NotFound();
            }

            var product = await _context.Products.FindAsync(id);
            if (product == null)
            {
                return NotFound();
            }
            return View(product);
        }

        // POST: Products/Edit/5
        // To protect from overposting attacks, enable the specific properties you want to bind to.
        // For more details, see http://go.microsoft.com/fwlink/?LinkId=317598.
        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> Edit(int id,  Product product)
        {
            if (id != product.ProductId)
            {
                return NotFound();
            }

            if (ModelState.IsValid)
            {
                try
                {
                    _context.Update(product);
                    await _context.SaveChangesAsync();
                }
                catch (DbUpdateConcurrencyException)
                {
                    if (!ProductExists(product.ProductId))
                    {
                        return NotFound();
                    }
                    else
                    {
                        throw;
                    }
                }
                return RedirectToAction(nameof(Index));
            }
            return View(product);
        }

        // GET: Products/Delete/5
        public async Task<IActionResult> Delete(int? id)
        {
            if (id == null)
            {
                return NotFound();
            }

            var product = await _context.Products
                .FirstOrDefaultAsync(m => m.ProductId == id);
            if (product == null)
            {
                return NotFound();
            }



            return View(product);
        }

        // POST: Products/Delete/5
        [HttpPost, ActionName("Delete")]
        [ValidateAntiForgeryToken]
        [Authorize(Roles = "Admin")]
        public async Task<IActionResult> DeleteConfirmed(int id)
        {
            var product = await _context.Products.FindAsync(id);
            if (product != null)
            {

                //also delete all orders related to the products
                var orders = await _context.OrderItems.AsNoTracking().Where(o => o.ProductId == id).ToListAsync();


                _context.OrderItems.RemoveRange(orders);
                _context.Products.Remove(product);
            }

            await _context.SaveChangesAsync();
            TempData["Message"] = "Product deleted successfully";

            return RedirectToAction(nameof(Admin));
        }

        [Authorize(Roles = "Admin")]
        public async Task<IActionResult> AdminDeleteAllProducts()
        {
            var products = await _context.Products.AsNoTracking().ToListAsync();

            var ids = products.Select(p => p.ProductId).ToList();

            //also delete all orders related to the products
            var orders = await _context.OrderItems.AsNoTracking().Where(o => ids.Contains(o.ProductId ?? 0)).ToListAsync();


            _context.OrderItems.RemoveRange(orders);
            _context.Products.RemoveRange(products);
            await _context.SaveChangesAsync();
            return RedirectToAction(nameof(Admin));
        }

        private bool ProductExists(int id)
        {
            return _context.Products.Any(e => e.ProductId == id);
        }
    }
}
