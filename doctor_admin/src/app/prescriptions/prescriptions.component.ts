import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { createClient } from '@supabase/supabase-js';
const supabaseUrl = 'https://eximxyncuxlgoqwvczmh.supabase.co';
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV4aW14eW5jdXhsZ29xd3Zjem1oIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU5MzM4NDEsImV4cCI6MjA2MTUwOTg0MX0.VpVEwWWm2NRUQrghAqhO5Pf5iuJU2cmZAao4-1b0NJc';
const supabase = createClient(supabaseUrl, supabaseAnonKey);

@Component({
  selector: 'app-prescriptions',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './prescriptions.component.html',
  styleUrl: './prescriptions.component.css'
})
export class PrescriptionsComponent {
  prescriptions: any[] = [];

  constructor() {
    this.loadPrescriptions();
  }

  async loadPrescriptions() {
    const { data, error } = await supabase
      .from('prescription')
      .select('*')
      .order('created_at', { ascending: false });

    if (error) {
      console.error('Error loading prescriptions:', error);
    } else {
      this.prescriptions = data || [];
    }
  }

}
