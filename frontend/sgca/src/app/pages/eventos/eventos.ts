import { Component, OnInit, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/apiservice';

@Component({
  selector: 'app-eventos',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule],
  templateUrl: './eventos.html',
  styleUrls: ['./eventos.css']
})
export class Eventos implements OnInit {
  
  private apiService = inject(ApiService);

  eventos = signal<any[]>([]);
  loading = signal(false);
  
  // Controle de Interface
  modoCriacao = false; // Se true, mostra o formulário
  idEmEdicao = signal(''); // Se tiver ID, é edição. Se vazio, é criação.
  
  // Feedback e Modal
  feedback = signal({ show: false, msg: '', type: 'success' });
  modalExclusao = signal({ show: false, id: '' });

  novoEvento = {
    titulo: '',
    organizador: '',
    descricao: '',
    local: '',
    data_inicio: '',
    data_fim: '',
    responsaveis_ids: [] as number[]
  };

  ngOnInit() {
    this.carregarEventos();
  }

  carregarEventos() {
    this.loading.set(true);
    console.log('🔄 Buscando eventos...');

    this.apiService.getEventos().subscribe({
      next: (dados) => {
        this.eventos.set(dados || []);
        this.loading.set(false);
      },
      error: (e) => {
        console.error('❌ Erro:', e);
        this.loading.set(false);
      }
    });
  }

  // 👇 NOVA FUNÇÃO: Prepara o formulário para edição
  editarEvento(evento: any) {
    this.idEmEdicao.set(evento.id);
    
    // Preenche os campos com os dados existentes
    this.novoEvento = {
      titulo: evento.titulo,
      organizador: evento.organizador || '',
      descricao: evento.descricao || '',
      local: evento.local,
      // O input datetime-local precisa do formato YYYY-MM-DDTHH:mm
      data_inicio: evento.data_inicio ? evento.data_inicio.slice(0, 16) : '',
      data_fim: evento.data_fim ? evento.data_fim.slice(0, 16) : '',
      responsaveis_ids: evento.responsaveis_ids || [1]
    };

    this.modoCriacao = true; // Abre o formulário
  }

  agendarEvento() {
    if (!this.novoEvento.titulo || !this.novoEvento.data_inicio || !this.novoEvento.data_fim) {
      alert('Preencha Título, Data de Início e Fim.');
      return;
    }

    this.loading.set(true);

    // Ajuste de datas (adiciona segundos para o Python)
    let inicio = this.novoEvento.data_inicio;
    let fim = this.novoEvento.data_fim;
    if (inicio.length === 16) inicio += ':00';
    if (fim.length === 16) fim += ':00';

    const payload = {
      ...this.novoEvento,
      descricao: this.novoEvento.descricao || 'Sem descrição',
      organizador: this.novoEvento.organizador || 'CA Geral',
      data_inicio: new Date(inicio).toISOString(),
      data_fim: new Date(fim).toISOString(),
      responsaveis_ids: [1],
      orcamento_limite: 0,
      status: 'Agendado' // Ou mantém o status anterior se quiser
    };

    // 👇 Decide se Cria ou Atualiza
    if (this.idEmEdicao()) {
      // ATUALIZAR
      this.apiService.updateEvento(this.idEmEdicao(), payload).subscribe({
        next: () => this.sucesso('Evento atualizado com sucesso!'),
        error: (e) => this.erro(e)
      });
    } else {
      // CRIAR
      this.apiService.createEvento(payload).subscribe({
        next: () => this.sucesso('Evento criado com sucesso!'),
        error: (e) => this.erro(e)
      });
    }
  }

  private sucesso(msg: string) {
    this.loading.set(false);
    this.mostrarNotificacao(msg, 'success');
    this.resetarForm();
    this.modoCriacao = false;
    this.carregarEventos();
  }

  private erro(e: any) {
    console.error(e);
    this.loading.set(false);
    this.mostrarNotificacao('Erro ao salvar evento.', 'error');
  }

  // --- MODAL, TOAST E RESETS ---

  abrirModalExclusao(id: string) {
    this.modalExclusao.set({ show: true, id: id });
  }

  fecharModal() {
    this.modalExclusao.set({ show: false, id: '' });
  }

  confirmarExclusao() {
    const id = this.modalExclusao().id;
    if (!id) return;
    this.fecharModal();
    this.loading.set(true);

    this.apiService.deleteEvento(id).subscribe({
      next: () => {
        this.carregarEventos();
        this.mostrarNotificacao('Evento cancelado!', 'success');
      },
      error: () => {
        this.loading.set(false);
        this.mostrarNotificacao('Erro ao excluir.', 'error');
      }
    });
  }

  mostrarNotificacao(mensagem: string, tipo: 'success' | 'error') {
    this.feedback.set({ show: true, msg: mensagem, type: tipo });
    setTimeout(() => this.feedback.set({ show: false, msg: '', type: 'success' }), 3000);
  }

  resetarForm() {
    this.idEmEdicao.set(''); // Limpa o ID
    this.novoEvento = {
      titulo: '',
      organizador: '',
      descricao: '',
      local: '',
      data_inicio: '',
      data_fim: '',
      responsaveis_ids: []
    };
  }
}