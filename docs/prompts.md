# Prompts

## Prompt 1
Preciso criar, testar e ao final, estando tudo correto, executar um CRUD simples para cadastrar apenas o nome do cliente, seu telefone e marcar se o telefone tem WhatsApp. Os dados serão persistidos em um arquivo texto nessa pasta.

**Required dependencies:**
- Ambiente virtual dotenv para rodar a aplicação.
- Utilize pytest para fazer os testes unitários.
- Por fim, execute o programa em um navegador.

---

## Prompt 2
Funcionou, porém o programa só está cadastrando e exibindo. Para um CRUD completo preciso que os dados possam ser também alterados e excluídos. Crie também os respectivos testes unitários para essas funcionalidades.

---

## Prompt 3
Ótimo, o CRUD está funcional, porém ele está com um layout muito "cru". Gostaria que aplicasse um CSS e deixasse ele mais apresentável.

- Coloque a exibição dos dados dentro de uma tabela.
- Onde se usa hiperlinks para editar, excluir ou cancelar, troque por botões ou ícones intuitivos.
- Alinhe os campos do cadastro.
- Troque o nome de "Cadastro de Clientes" para "Agenda Pessoal".

---

## Prompt 4
- Alinhe o botão cadastrar abaixo do campo WhatsApp.
- Desabilite que ao clicar na tecla Enter, ele clique automaticamente em cadastrar.

---

## Prompt 5
- Alargue lateralmente o painel e a tabela de forma que na exibição os números de telefone, nomes não muito extensos, telefones e botões ocupem apenas uma única linha por registro.

---

## Prompt 6
Adicione as seguintes regras de validação no cadastro que exibam mensagens na tela caso ocorram:
- Não existe cadastro vazio (sem nome e telefone).
- É obrigatório cadastrar ao menos um nome, caso não seja informado.
- O contato deve ter um telefone, caso esse não seja informado.
- Quando alguma dessas situações ocorrer, a mensagem deve ser exibida e não permitir o cadastro ou alteração.
- Assim que os campos forem devidamente preenchidos e o botão cadastrar ou salvar forem clicados, a ação será realizada normalmente.
