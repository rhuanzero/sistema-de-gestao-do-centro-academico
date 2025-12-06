import { Component } from '@angular/core';
import { CommonModule } from '@angular/common'; // <--- Adicione isso

@Component({
  selector: 'app-home',
  imports: [CommonModule], // <--- Adicione isso aqui também
  templateUrl: './home.html',
  styleUrl: './home.css', // ⚠️ Atenção: em algumas versões é 'styleUrls' (array), verifique se não dá erro
})
export class Home {
}