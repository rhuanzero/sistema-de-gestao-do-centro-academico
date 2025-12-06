import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-eventos',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './eventos.html',
  styleUrl: './eventos.css'
})
export class Eventos {
  events = [
    { title: 'Recepção dos Calouros', day: '25', month: 'Out', location: 'Auditório 2', status: 'Confirmado' },
    { title: 'Workshop de Python', day: '10', month: 'Nov', location: 'Lab 3', status: 'Planejamento' },
  ];
}