using Microsoft.AspNetCore.SignalR;
using System.Threading.Tasks;

public class SensorHub : Hub
{
    public async Task SendSensorData(float value, string timestamp)
    {
        await Clients.All.SendAsync("ReceiveSensorData", value, timestamp);
    }
}
