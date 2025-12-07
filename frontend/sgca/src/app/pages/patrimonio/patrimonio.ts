import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';

// IMPORTANTE: Ajuste o caminho para onde está seu Service e Model unificados
import { ApiService } from '../../services/apiservice'; 
import { Patrimonio } from '../../models/api'; 

@Component({
  selector: 'app-patrimonio',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './patrimonio.html',
  styleUrls: ['./patrimonio.css'] // Opcional se tiver CSS específico
})
export class PatrimonioComponent implements OnInit {
  itens: Patrimonio[] = [];
  form: FormGroup;
  
  // Controle de estado da tela
  loading = false;
  erro = '';
  modoEdicao = false;
  idEmEdicao: string | null = null;

  constructor(
    private apiService: ApiService, // Seu service unificado
    private fb: FormBuilder,
    private cdRef: ChangeDetectorRef
  ) {
    // Definição do Formulário com validações
    this.form = this.fb.group({
      nome: ['', [Validators.required, Validators.minLength(3)]],
      tombo: [''], // Opcional
      valor: [0, [Validators.required, Validators.min(0)]],
      estado: ['Bom', Validators.required],
      localizacao: ['Sede do CA', Validators.required]
    });
  }

  ngOnInit(): void {
    this.carregarPatrimonio();
  }

carregarPatrimonio() {
    this.loading = true;
    this.apiService.getPatrimonios().subscribe({
      next: (dados) => {
        this.itens = dados;
        this.loading = false;
        
        // 3. ADICIONE ESSA LINHA PARA CORRIGIR O ERRO NG0100
        this.cdRef.detectChanges(); 
      },
      error: (e) => {
        console.error(e);
        this.erro = 'Erro ao carregar lista de patrimônio.';
        this.loading = false;
        
        // Adicione aqui também por garantia
        this.cdRef.detectChanges();
      }
    });
  }

  onSubmit() {
    if (this.form.invalid) return;

    this.loading = true;
    const item: Patrimonio = this.form.value;

    if (this.modoEdicao && this.idEmEdicao) {
      // ATUALIZAR
      this.apiService.updatePatrimonio(this.idEmEdicao, item).subscribe({
        next: () => {
          this.sucessoOperacao();
        },
        error: (err) => {
          this.erro = 'Erro ao atualizar item.';
          this.loading = false;
        }
      });
    } else {
      // CRIAR NOVO
      this.apiService.createPatrimonio(item).subscribe({
        next: () => {
          this.sucessoOperacao();
        },
        error: (err) => {
          this.erro = 'Erro ao cadastrar item.';
          this.loading = false;
        }
      });
    }
  }

  editar(item: Patrimonio) {
    this.modoEdicao = true;
    this.idEmEdicao = item.id || null;
    
    // Preenche o formulário com os dados do item clicado
    this.form.patchValue({
      nome: item.nome,
      tombo: item.tombo,
      valor: item.valor,
      estado: item.estado,
      localizacao: item.localizacao
    });
    
    // Rola a página para o topo (formulário) em mobile
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  deletar(id: string) {
    if (confirm('Tem certeza que deseja dar baixa/excluir este item do patrimônio?')) {
      this.loading = true;
      this.apiService.deletePatrimonio(id).subscribe({
        next: () => {
          this.carregarPatrimonio(); // Recarrega a lista
        },
        error: () => {
          this.erro = 'Erro ao excluir item.';
          this.loading = false;
        }
      });
    }
  }

  cancelarEdicao() {
    this.modoEdicao = false;
    this.idEmEdicao = null;
    this.form.reset({
      estado: 'Bom',
      localizacao: 'Sede do CA',
      valor: 0
    });
    this.erro = '';
  }

  private sucessoOperacao() {
    this.carregarPatrimonio();
    this.cancelarEdicao(); // Limpa form e estado
    this.loading = false;
  }
}