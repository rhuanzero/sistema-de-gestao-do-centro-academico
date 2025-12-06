import { Component } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router'; // <--- Importe estes 3
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-root',
  standalone: true,
  // Adicione nos imports:
  imports: [CommonModule, RouterOutlet, RouterLink, RouterLinkActive], 
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {
  title = 'SGCA';
}