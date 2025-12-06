import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-patrimonio',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './patrimonio.html',
  styleUrl: './patrimonio.css'
})
export class Patrimonio { // <--- Ajustado aqui
  assets = [
    { id: '001', name: 'Notebook Dell Inspiron', location: 'Presidência', value: '3.500', condition: 'Bom' },
    { id: '002', name: 'Cafeteira Três Corações', location: 'Copa', value: '350', condition: 'Novo' },
    { id: '003', name: 'Sofá 3 Lugares', location: 'Área Comum', value: '1.200', condition: 'Danificado' },
    { id: '004', name: 'Projetor Epson', location: 'Armário 1', value: '2.800', condition: 'Bom' },
  ];
}