using System.Collections.Generic;

namespace CPRM2.Models
{
    public class AdminDashboardViewModel
    {
  public int TotalAgents { get; set; }
        public int PendingVerifications { get; set; }
        public List<Order> RecentOrders { get; set; }
        public List<ChatbotLog> RecentChatLogs { get; set; }
        public int TotalOrders { get; internal set; }
        public int TotalProducts { get; internal set; }
        public double TotalInventory { get; internal set; }
        public int TotalUsers { get; internal set; }
        public int TotalAdmins { get; internal set; }
        public List<Product> LowStockProducts { get; internal set; }
        public double TotalRevenue { get; internal set; }
    }
}