using Microsoft.AspNetCore.Identity;
using Microsoft.EntityFrameworkCore;
using CPRM2.Data;
using CPRM2.Areas.Identity.Data;
var builder = WebApplication.CreateBuilder(args);
var connectionString = builder.Configuration.GetConnectionString("dbcontext") ?? throw new InvalidOperationException("Connection string 'CPRM2IdentityContextConnection' not found.");

builder.Services.AddDbContext<CPRM2IdentityContext>(options => options.UseSqlServer(connectionString));
builder.Services.AddDbContext<CprmDbContext>(options => options.UseSqlServer(connectionString));

builder.Services.AddDefaultIdentity<CPRM2User>(options => options.SignIn.RequireConfirmedAccount = true)
    .AddRoles<IdentityRole>() // Ensure this line is here
    .AddEntityFrameworkStores<CPRM2IdentityContext>();

// Add services to the container.
builder.Services.AddControllersWithViews();

// Add session support
builder.Services.AddDistributedMemoryCache();
builder.Services.AddSession(options =>
{
    options.IdleTimeout = TimeSpan.FromMinutes(30);
    options.Cookie.HttpOnly = true;
    options.Cookie.IsEssential = true;
});

var app = builder.Build();

// Configure the HTTP request pipeline.
if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Home/Error");
    // The default HSTS value is 30 days. You may want to change this for production scenarios, see https://aka.ms/aspnetcore-hsts.
    app.UseHsts();
}

app.UseHttpsRedirection();
app.UseStaticFiles();

app.UseRouting();
app.UseSession(); // Enable session middleware
app.MapRazorPages();
app.UseAuthentication();
app.UseAuthorization();

app.MapControllerRoute(
    name: "default",
    pattern: "{controller=Home}/{action=Index}/{id?}");

app.Run();
