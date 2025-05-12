import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { createClient } from '@supabase/supabase-js';


const supabaseUrl = 'https://eximxyncuxlgoqwvczmh.supabase.co';
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV4aW14eW5jdXhsZ29xd3Zjem1oIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU5MzM4NDEsImV4cCI6MjA2MTUwOTg0MX0.VpVEwWWm2NRUQrghAqhO5Pf5iuJU2cmZAao4-1b0NJc';
const supabase = createClient(supabaseUrl, supabaseAnonKey);

@Component({
  selector: 'app-user-registration',
  standalone: true,
  imports: [FormsModule, CommonModule],
  templateUrl: './user-registration.component.html',
  styleUrls: ['./user-registration.component.css',]
})
export class UserRegistrationComponent {
  email: string = '';
  password: string = '';
  confirmPassword: string = '';
  errorMessage: string = '';
  successMessage: string = '';

  async register() {
    if (this.password !== this.confirmPassword) {
      this.errorMessage = 'Passwords do not match';
      return;
    }

    const { error } = await supabase.auth.signUp({
      email: this.email,
      password: this.password
    });

    if (error) {
      this.errorMessage = error.message;
    } else {
      this.successMessage = 'Registration successful!';
      this.errorMessage = '';
    }
  }
}