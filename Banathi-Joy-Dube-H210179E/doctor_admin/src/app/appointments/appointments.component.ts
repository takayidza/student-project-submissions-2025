import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { createClient } from '@supabase/supabase-js';

// Supabase configuration (replace with your actual URL and key if different)
const supabaseUrl = 'https://eximxyncuxlgoqwvczmh.supabase.co';
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV4aW14eW5jdXhsZ29xd3Zjem1oIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU5MzM4NDEsImV4cCI6MjA2MTUwOTg0MX0.VpVEwWWm2NRUQrghAqhO5Pf5iuJU2cmZAao4-1b0NJc';
const supabase = createClient(supabaseUrl, supabaseAnonKey);

@Component({
  selector: 'app-appointments',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './appointments.component.html',
  styleUrl: './appointments.component.css'
})
export class AppointmentsComponent implements OnInit {
  appointments: any[] = [];

  async ngOnInit() {
    await this.fetchAppointments();
  }

  async fetchAppointments() {
    const { data, error } = await supabase
      .from('appointments')
      .select('*');

    if (error) {
      console.error('Error fetching appointments:', error);
    } else {
      console.log('Data received from Supabase:', data);
      console.log('Number of appointments fetched from Supabase:', data ? data.length : 0);
      this.appointments = data || [];
      console.log('Appointments assigned to component property:', this.appointments);
      console.log('Number of appointments in component property:', this.appointments.length);
    }
  }
  
  async acceptAppointment(appointmentId: number) {
    try {
      const { data, error } = await supabase
        .from('appointments')
          .update({ status: 'confirmed' })
          .eq('id', appointmentId);
  
        if (error) {
          console.error('Error accepting appointment:', error);
          return;
        }
  
        // Refresh the appointments list after successful update
        await this.fetchAppointments();
  
      } catch (err) {
        console.error('Error accepting appointment:', err);
      }
    }
    }


