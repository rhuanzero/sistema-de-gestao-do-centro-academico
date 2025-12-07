import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms'; // <--- Não esqueça!
import { ApiService } from '../../services/apiservice';

@Component({
  selector: 'app-eventos',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './eventos.html',
  styleUrls: ['./eventos.css']
})
export class Eventos implements OnInit {

  eventos: any[] = [];
  mostrarModal = false;
  
  // Objeto do formulário
novoEvento = {
    titulo: '',
    descricao: '',
    data_inicio: '', // Mudou: Antes era só 'data'
    data_fim: '',    // Novo campo
    local: '',
    organizador: '',
    responsaveis_ids: [] // Novo campo (Backend exige)
  };

  constructor(private apiService: ApiService) {}

  ngOnInit() {
    this.carregarEventos();
  }

  carregarEventos() {
    this.apiService.getEvents().subscribe({
      next: (dados) => {
        console.log('Eventos carregados:', dados);
        this.eventos = dados;
      },
      error: (e) => console.error('Erro ao carregar eventos:', e)
    });
  }

 abrirModal() {
    this.novoEvento = { 
      titulo: '', 
      descricao: '', 
      data_inicio: '', 
      data_fim: '', 
      local: '', 
      organizador: '',
      responsaveis_ids: [] 
    };
    this.mostrarModal = true;
  }

  salvar() {
    // Validação básica
    if (!this.novoEvento.titulo || !this.novoEvento.data_inicio || !this.novoEvento.data_fim) {
      alert('Preencha título, início e fim!');
      return;
    }

    // Prepara o Payload (JSON) que o Python quer
    const payload = {
      titulo: this.novoEvento.titulo,
      descricao: this.novoEvento.descricao,
      local: this.novoEvento.local,
      organizador: this.novoEvento.organizador,
      
      // Converte as duas datas para ISO String
      data_inicio: new Date(this.novoEvento.data_inicio).toISOString(),
      data_fim: new Date(this.novoEvento.data_fim).toISOString(),
      
      // Envia array vazio para satisfazer o Pydantic (ou coloque IDs reais se tiver)
      responsaveis_ids: [] 
    };

    console.log('Enviando:', payload); // Debug

    this.apiService.createEvent(payload).subscribe({
      next: () => {
        alert('Evento criado com sucesso!');
        this.mostrarModal = false;
        this.carregarEventos();
      },
      error: (e) => {
        console.error(e);
        const msg = e.error.detail ? JSON.stringify(e.error.detail) : e.message;
        alert('Erro ao criar evento: ' + msg);
      }
    });
  }

excluir(id: string) {
    if (confirm('Tem certeza que deseja cancelar este evento?')) {
      this.apiService.deleteEvent(id).subscribe({
        next: () => {
          this.carregarEventos(); // Sucesso normal
        },
        error: (e) => {
          // SE O ERRO FOR 404, SIGNIFICA QUE JÁ FOI APAGADO.
          // ENTÃO ATUALIZAMOS A LISTA MESMO ASSIM.
          if (e.status === 404) {
            console.warn('Evento não existia mais, atualizando lista...');
            this.carregarEventos(); 
          } else {
            alert('Erro ao excluir: ' + e.message);
          }
        }
      });
    }
  }
}