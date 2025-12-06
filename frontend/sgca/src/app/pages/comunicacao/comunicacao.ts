import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-comunicacao',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './comunicacao.html',
  styleUrl: './comunicacao.css'
})
export class Comunicacao { // <--- Ajustado aqui
  posts = [
    { title: 'Divulgação Festa Junina', platform: 'Instagram', date: '20/10/2025', status: 'Agendado' },
    { title: 'Parceria Alura', platform: 'LinkedIn', date: '15/10/2025', status: 'Publicado' },
    { title: 'Aviso de Greve', platform: 'Instagram', date: '10/10/2025', status: 'Publicado' },
  ];

  docs = [
    { title: 'Ata de Reunião 04/2025', date: '18/10/2025', author: 'Secretaria' },
    { title: 'Ofício Solicitação Auditório', date: '12/10/2025', author: 'Presidência' },
  ];
}