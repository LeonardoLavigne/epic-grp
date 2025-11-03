# Epic GRP Frontend

Stack:
- Vite + React + TypeScript
- React Router
- TanStack Query
- Axios (com Authorization)

Scripts:
- `npm run dev` — dev server (VITE_API_URL para apontar para o backend)
- `npm run build` — build
- `npm run preview` — preview do build

Env:
- `VITE_API_URL` (ex.: http://localhost:8000)

Páginas e Notas
- Auth: Login, Registro
- Finanças: Contas, Categorias, Transações, Transferências, Relatórios
- Observabilidade: indicador /ready e ReqID
- Transações: itens com `from_transfer=true` (vindos de Transferências) são somente leitura nesta tela; ações como Void/edição permanecem desabilitadas. Para anulá-las, utilize o fluxo de Transferências.
