import { Component } from '@angular/core';
import { RouterOutlet} from '@angular/router'; // <--- Importe estes 3
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-root',
  standalone: true,
  // Adicione nos imports:
  imports: [CommonModule, RouterOutlet, FormsModule], 
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {
  title = 'SGCA';
}