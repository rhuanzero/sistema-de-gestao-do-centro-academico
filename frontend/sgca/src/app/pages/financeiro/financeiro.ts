import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-financeiro',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './financeiro.html',
  styleUrl: './financeiro.css'
})
export class Financeiro {
  transactions = [
    { desc: 'Venda de Kits Bixo', date: '18/10/2025', value: 1500, type: 'in' },
    { desc: 'Compra de Material Escritório', date: '17/10/2025', value: 250, type: 'out' },
    { desc: 'Patrocínio Alura', date: '15/10/2025', value: 1700, type: 'in' },
  ];
}