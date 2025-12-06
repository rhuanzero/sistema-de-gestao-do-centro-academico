import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-membros',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './membros.html',
  styleUrl: './membros.css'
})
export class Membros {
  members = [
    { name: 'Thauan', role: 'Presidente', course: 'Sistemas de Info.', active: true },
    { name: 'Maria Silva', role: 'Tesoureira', course: 'Eng. Software', active: true },
    { name: 'João Souza', role: 'Membro', course: 'Ciência Comp.', active: false },
  ];
}