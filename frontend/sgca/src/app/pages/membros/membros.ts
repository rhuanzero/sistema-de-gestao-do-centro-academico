import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { FormsModule } from '@angular/forms'; // <--- IMPORTANTE: Adicione isso!
import { Router } from '@angular/router';

interface Membro {
  id: number | null; // Pode ser null na criação
  nome: string;
  email: string;
  cargo: string;
  status: string;
  telefone?: string;
  cpf?: string;
  senha?: string; // Opcional, usado só no envio
}

@Component({
  selector: 'app-membros',
  standalone: true,
  imports: [CommonModule, FormsModule], // <--- Adicione FormsModule aqui
  templateUrl: './membros.html',
  styleUrls: ['./membros.css']
})
export class Membros implements OnInit {
  private http = inject(HttpClient);
  private apiUrl = 'http://localhost:8000/membros'; // Verifique se é /members ou /membros
  private router = inject(Router);

  // Signals de Dados
  membros = signal<Membro[]>([]);
  loading = signal(false);
  cargoUsuarioLogado = signal<string>('');
  
  // Signals de Controle Visual
  modalFormAberto = signal(false);
  modalDeleteAberto = signal(false);
  modoEdicao = signal(false); // false = Criando, true = Editando

  // Dados do Formulário
  novoMembro: Membro = this.getEmptyMembro();
  membroParaExclusao: Membro | null = null;

  ehPresidente = computed(() => {
    return this.cargoUsuarioLogado().toLowerCase() === 'presidente';
  });

 ngOnInit() {
  this.carregarUsuarioLogado();
  
  // ADICIONE ESSA LINHA PARA TESTAR 👇
  console.log('Cargo no LocalStorage:', localStorage.getItem('user_role'));
  console.log('Sou presidente?', this.ehPresidente());
  
  this.buscarMembros();
}

  carregarUsuarioLogado() {
    const role = localStorage.getItem('user_role') || '';
    this.cargoUsuarioLogado.set(role);
  }

  buscarMembros() {
    this.loading.set(true);
    this.http.get<Membro[]>(this.apiUrl).subscribe({
      next: (data) => {
        this.membros.set(data);
        this.loading.set(false);
      },
      error: (err) => {
        console.error('Erro ao buscar membros', err);
        this.loading.set(false);
      }
    });
  }

  // --- AÇÕES DO MODAL DE FORMULÁRIO (CRIAR/EDITAR) ---

  abrirModalCadastro() {
    if (!this.ehPresidente()) return;
    this.modoEdicao.set(false);
    this.novoMembro = this.getEmptyMembro();
    this.modalFormAberto.set(true);
  }

  editarMembro(membro: Membro) {
    if (!this.ehPresidente()) return;
    this.modoEdicao.set(true);
    // Copia os dados para não alterar a tabela em tempo real antes de salvar
    this.novoMembro = { ...membro, senha: '' }; 
    this.modalFormAberto.set(true);
  }

  fecharModalForm() {
    this.modalFormAberto.set(false);
  }

  salvarMembro() {
    this.loading.set(true);

    if (this.modoEdicao() && this.novoMembro.id) {
      // --- EDIÇÃO (PUT) ---
      this.http.put<Membro>(`${this.apiUrl}/${this.novoMembro.id}`, this.novoMembro).subscribe({
        next: (membroAtualizado) => {
          this.membros.update(lista => lista.map(m => m.id === membroAtualizado.id ? membroAtualizado : m));
          this.loading.set(false);
          this.fecharModalForm();
          alert('Membro atualizado!');
        },
        error: (err) => {
          console.error(err);
          this.loading.set(false);
          alert('Erro ao atualizar. Verifique os dados.');
        }
      });
    } else {
      // --- CRIAÇÃO (POST) ---
      // Garante que o ID não vai no envio se for criação
      const { id, ...payload } = this.novoMembro;
      
      this.http.post<Membro>(this.apiUrl, payload).subscribe({
        next: (novoMembroCriado) => {
          this.membros.update(lista => [...lista, novoMembroCriado]);
          this.loading.set(false);
          this.fecharModalForm();
          alert('Membro criado com sucesso!');
        },
        error: (err) => {
          console.error(err);
          this.loading.set(false);
          alert('Erro ao criar membro. Email ou CPF já existem?');
        }
      });
    }
  }

  // --- AÇÕES DO MODAL DE EXCLUSÃO ---

  prepararExclusao(membro: Membro) {
    if (!this.ehPresidente()) return;
    this.membroParaExclusao = membro;
    this.modalDeleteAberto.set(true);
  }

  confirmarExclusao() {
    if (!this.membroParaExclusao?.id) return;

    this.loading.set(true);
    this.http.delete(`${this.apiUrl}/${this.membroParaExclusao.id}`).subscribe({
      next: () => {
        this.membros.update(lista => lista.filter(m => m.id !== this.membroParaExclusao!.id));
        this.loading.set(false);
        this.fecharModalDelete();
      },
      error: (err) => {
        console.error(err);
        this.loading.set(false);
        alert('Erro ao excluir.');
      }
    });
  }

  fecharModalDelete() {
    this.modalDeleteAberto.set(false);
    this.membroParaExclusao = null;
  }

  // --- UTILITÁRIOS ---

  private getEmptyMembro(): Membro {
    return {
      id: null,
      nome: '',
      email: '',
      cargo: 'Membro', // Valor padrão
      status: 'Ativo',
      cpf: '',
      telefone: '',
      senha: ''
    };
  }

  getStatusClass(status: string): string {
    return status === 'Ativo' ? 'status-published' : 'status-cancelled';
  }

  logout() {
    // Limpa tudo do navegador
    localStorage.clear();
    
    // Manda o usuário de volta pro login
    this.router.navigate(['/login']);
  }
}