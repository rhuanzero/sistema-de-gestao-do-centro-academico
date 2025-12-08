import { Component, OnInit, inject, signal, WritableSignal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http'; // Importar HttpClient

// Defina a URL do seu backend aqui
const API_URL = 'http://localhost:8000';

export interface Post {
  id?: number; // Opcional na criação
  titulo: string;
  midia_destino: string;
  data_agendamento: string;
  status: string;
  conteudo?: string;
}

export interface Solicitacao {
  id?: number;
  titulo: string;
  solicitante_nome: string;
  prazo_sugerido: string;
  status: string;
  conteudo?: string;
}

@Component({
  selector: 'app-comunicacao',
  standalone: true,
  imports: [CommonModule, FormsModule], // HttpClientModule não é necessário aqui no Standalone moderno, mas veja a obs no final
  templateUrl: './comunicacao.html',
  styleUrls: ['./comunicacao.css']
})
export class Comunicacao implements OnInit {
  
  // Injeção de dependência do HTTP
  private http = inject(HttpClient);

  // Signals de Estado
  loading = signal(false);
  
  // Dados (Inicializam VAZIOS, pois virão do back)
  posts = signal<Post[]>([]);
  docs = signal<Solicitacao[]>([]);

  // Controle de Modais
  modalAberto = signal(false);
  modoEdicao = signal(false);
  
  modalExclusaoAberto = signal(false);
  itemParaExclusao = signal<any>(null);
  tipoParaExclusao = signal<string>('');

  // Formulário
  tipoItem = 'post';
  novoItem: any = this.getEmptyItem();

  // --- CICLO DE VIDA ---
  ngOnInit() {
    this.carregarDados();
  }

  // --- BUSCA DE DADOS (GET) ---
  carregarDados() {
    this.loading.set(true);

    // Busca Postagens
    this.http.get<Post[]>(`${API_URL}/postagens`).subscribe({
      next: (data) => this.posts.set(data),
      error: (err) => console.error('Erro ao buscar posts', err)
    });

    // Busca Solicitações
    this.http.get<Solicitacao[]>(`${API_URL}/solicitacoes`).subscribe({
      next: (data) => this.docs.set(data),
      error: (err) => console.error('Erro ao buscar docs', err),
      complete: () => this.loading.set(false) // Tira o loading quando terminar
    });
  }

  // --- MÉTODOS DE MODAL ---
  abrirModalCriacao() {
    this.modoEdicao.set(false);
    this.resetarForm();
    this.modalAberto.set(true);
  }

  fecharModal() {
    this.modalAberto.set(false);
  }

  resetarForm() {
    this.novoItem = this.getEmptyItem();
  }

  private getEmptyItem() {
    return { id: null, titulo: '', conteudo: '', data: '', extra: '', status: 'Rascunho' };
  }

  // --- PREPARAR EDIÇÃO ---
  editarItem(item: any, tipo: string) {
    this.modoEdicao.set(true);
    this.tipoItem = tipo;
    
    // Mapeia os dados do objeto real para o formato do formulário
    this.novoItem = {
      id: item.id,
      titulo: item.titulo,
      conteudo: item.conteudo || '',
      status: item.status,
      data: tipo === 'post' ? item.data_agendamento : item.prazo_sugerido,
      extra: tipo === 'post' ? item.midia_destino : (item.solicitante_nome || '')
    };

    this.modalAberto.set(true);
  }

  // --- SALVAR (POST ou PUT) ---
  salvarItem() {
    this.loading.set(true);
    
    // Monta o objeto correto para enviar ao Back
    let payload: any;
    let endpoint = '';

    if (this.tipoItem === 'post') {
      endpoint = `${API_URL}/postagens`;
      payload = {
        titulo: this.novoItem.titulo,
        midia_destino: this.novoItem.extra,
        data_agendamento: this.novoItem.data,
        status: this.novoItem.status,
        conteudo: this.novoItem.conteudo
      } as Post;
    } else {
      endpoint = `${API_URL}/solicitacoes`;
      payload = {
        titulo: this.novoItem.titulo,
        solicitante_nome: 'Usuário Atual', // Você pode pegar isso de um AuthService depois
        prazo_sugerido: this.novoItem.data,
        status: this.novoItem.status,
        conteudo: this.novoItem.conteudo
      } as Solicitacao;
    }

    // Verifica se é Edição (PUT) ou Criação (POST)
    if (this.modoEdicao() && this.novoItem.id) {
      // --- UPDATE ---
      this.http.put(`${endpoint}/${this.novoItem.id}`, payload).subscribe({
        next: (itemAtualizado: any) => {
          // Atualiza a lista localmente para não precisar recarregar tudo
          if (this.tipoItem === 'post') {
            this.posts.update(lista => lista.map(p => p.id === itemAtualizado.id ? itemAtualizado : p));
          } else {
            this.docs.update(lista => lista.map(d => d.id === itemAtualizado.id ? itemAtualizado : d));
          }
          this.sucessoOperacao();
        },
        error: (err) => this.tratarErro(err)
      });
    } else {
      // --- CREATE ---
      this.http.post(endpoint, payload).subscribe({
        next: (novoItemCriado: any) => {
          // Adiciona na lista local
          if (this.tipoItem === 'post') {
            this.posts.update(lista => [...lista, novoItemCriado]);
          } else {
            this.docs.update(lista => [...lista, novoItemCriado]);
          }
          this.sucessoOperacao();
        },
        error: (err) => this.tratarErro(err)
      });
    }
  }

  private sucessoOperacao() {
    this.loading.set(false);
    this.fecharModal();
    // Opcional: Adicionar um Toast de sucesso aqui
  }

  private tratarErro(err: any) {
    console.error(err);
    this.loading.set(false);
    alert('Erro ao salvar item. Verifique o console.');
  }

  // --- EXCLUSÃO (DELETE) ---
  
  prepararExclusao(item: any, tipo: string) {
    this.itemParaExclusao.set(item);
    this.tipoParaExclusao.set(tipo);
    this.modalExclusaoAberto.set(true);
  }

  confirmarExclusao() {
    const item = this.itemParaExclusao();
    const tipo = this.tipoParaExclusao();

    if (!item) return;

    this.loading.set(true);
    const endpoint = tipo === 'post' ? `${API_URL}/postagens` : `${API_URL}/solicitacoes`;

    this.http.delete(`${endpoint}/${item.id}`).subscribe({
      next: () => {
        // Remove da lista local
        if (tipo === 'post') {
          this.posts.update(lista => lista.filter(p => p.id !== item.id));
        } else {
          this.docs.update(lista => lista.filter(d => d.id !== item.id));
        }
        
        this.loading.set(false);
        this.fecharModalExclusao();
      },
      error: (err) => {
        console.error('Erro ao excluir', err);
        this.loading.set(false);
        alert('Não foi possível excluir.');
      }
    });
  }

  fecharModalExclusao() {
    this.modalExclusaoAberto.set(false);
    this.itemParaExclusao.set(null);
  }

  // --- UTILITÁRIOS ---
  getStatusClass(status: string): string {
    if (!status) return 'status-draft';
    const s = status.toLowerCase();
    if (s.includes('publicado') || s.includes('aprovado')) return 'status-published';
    if (s.includes('agendado')) return 'status-scheduled';
    if (s.includes('cancelado') || s.includes('rejeitado')) return 'status-cancelled';
    return 'status-draft';
  }
}