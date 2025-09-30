let s:cpo_save=&cpo
set cpo&vim
cnoremap <silent> <Plug>(TelescopeFuzzyCommandSearch) e "lua require('telescope.builtin').command_history { default_text = [=[" . escape(getcmdline(), '"') . "]=] }"
inoremap <C-W> u
inoremap <C-U> u
nnoremap  <Cmd>nohlsearch|diffupdate|normal! 
nmap  d
tnoremap  
nnoremap  d :lua vim.diagnostic.open_float(nil, {focus=true, scope="cursor", close_events={"BufLeave", "CursorMoved"}})
nnoremap  f :Telescope file_browser path=%:p:h select_buffer=true
nnoremap  a :Telescope aerial
nnoremap  T :TodoQuickFix
nnoremap  t :TodoTelescope
nnoremap  fg :lua require("telescope").extensions.live_grep_args.live_grep_args({debounce = 100})
nnoremap  r :Telescope resume
nnoremap <silent>  nf :lua require('neogen').generate()
nnoremap <silent>   <Nop>
omap <silent> % <Plug>(MatchitOperationForward)
xmap <silent> % <Plug>(MatchitVisualForward)
nmap <silent> % <Plug>(MatchitNormalForward)
nnoremap & :&&
xnoremap <silent> <expr> @ mode() ==# 'V' ? ':normal! @'.getcharstr().'' : '@'
nnoremap K <Cmd>Man
xnoremap <silent> <expr> Q mode() ==# 'V' ? ':normal! @=reg_recorded()' : 'Q'
nnoremap Y y$
omap <silent> [% <Plug>(MatchitOperationMultiBackward)
xmap <silent> [% <Plug>(MatchitVisualMultiBackward)
nmap <silent> [% <Plug>(MatchitNormalMultiBackward)
omap <silent> ]% <Plug>(MatchitOperationMultiForward)
xmap <silent> ]% <Plug>(MatchitVisualMultiForward)
nmap <silent> ]% <Plug>(MatchitNormalMultiForward)
xmap a% <Plug>(MatchitVisualTextObject)
omap <silent> g% <Plug>(MatchitOperationBackward)
xmap <silent> g% <Plug>(MatchitVisualBackward)
nmap <silent> g% <Plug>(MatchitNormalBackward)
nnoremap gs :TSJSplit
nnoremap gj :TSJJoin
xmap <silent> <Plug>(MatchitVisualTextObject) <Plug>(MatchitVisualMultiBackward)o<Plug>(MatchitVisualMultiForward)
onoremap <silent> <Plug>(MatchitOperationMultiForward) :call matchit#MultiMatch("W",  "o")
onoremap <silent> <Plug>(MatchitOperationMultiBackward) :call matchit#MultiMatch("bW", "o")
xnoremap <silent> <Plug>(MatchitVisualMultiForward) :call matchit#MultiMatch("W",  "n")m'gv``
xnoremap <silent> <Plug>(MatchitVisualMultiBackward) :call matchit#MultiMatch("bW", "n")m'gv``
nnoremap <silent> <Plug>(MatchitNormalMultiForward) :call matchit#MultiMatch("W",  "n")
nnoremap <silent> <Plug>(MatchitNormalMultiBackward) :call matchit#MultiMatch("bW", "n")
onoremap <silent> <Plug>(MatchitOperationBackward) :call matchit#Match_wrapper('',0,'o')
onoremap <silent> <Plug>(MatchitOperationForward) :call matchit#Match_wrapper('',1,'o')
xnoremap <silent> <Plug>(MatchitVisualBackward) :call matchit#Match_wrapper('',0,'v')m'gv``
xnoremap <silent> <Plug>(MatchitVisualForward) :call matchit#Match_wrapper('',1,'v'):if col("''") != col("$") | exe ":normal! m'" | endifgv``
nnoremap <silent> <Plug>(MatchitNormalBackward) :call matchit#Match_wrapper('',0,'n')
nnoremap <silent> <Plug>(MatchitNormalForward) :call matchit#Match_wrapper('',1,'n')
nnoremap <Plug>PlenaryTestFile :lua require('plenary.test_harness').test_file(vim.fn.expand("%:p"))
nmap <C-W><C-D> d
nnoremap <C-L> <Cmd>nohlsearch|diffupdate|normal! 
inoremap  u
inoremap  u
let &cpo=s:cpo_save
unlet s:cpo_save
set clipboard=unnamed,unnamedplus
set grepformat=%f:%l:%c:%m
set grepprg=rg\ --vimgrep\ -uu\ 
set helplang=en
set indentkeys=0{,0},0),0],:,0#,!^F,o,O,e,0],0)
set laststatus=3
set noloadplugins
set packpath=/usr/share/nvim/runtime
set runtimepath=~/.config/nvim,~/.local/share/nvim/lazy/lazy.nvim,~/.local/share/nvim/lazy/markview.nvim,~/.local/share/nvim/lazy/cmp_luasnip,~/.local/share/nvim/lazy/LuaSnip,~/.local/share/nvim/lazy/cmp-cmdline,~/.local/share/nvim/lazy/cmp-path,~/.local/share/nvim/lazy/cmp-buffer,~/.local/share/nvim/lazy/cmp-nvim-lsp,~/.local/share/nvim/lazy/nvim-lspconfig,~/.local/share/nvim/lazy/nvim-cmp,~/.local/share/nvim/lazy/lualine.nvim,~/.local/share/nvim/lazy/telescope-file-browser.nvim,~/.local/share/nvim/lazy/mason-lspconfig.nvim,~/.local/share/nvim/lazy/mason.nvim,~/.local/share/nvim/lazy/nvim-web-devicons,~/.local/share/nvim/lazy/aerial.nvim,~/.local/share/nvim/lazy/todo-comments.nvim,~/.local/share/nvim/lazy/telescope-fzf-native.nvim,~/.local/share/nvim/lazy/plenary.nvim,~/.local/share/nvim/lazy/telescope.nvim,~/.local/share/nvim/lazy/telescope-live-grep-args.nvim,~/.local/share/nvim/lazy/nvim-treesitter,~/.local/share/nvim/lazy/treesj,~/.local/share/nvim/lazy/indent-blankline.nvim,~/.local/share/nvim/lazy/neogen,~/.local/share/nvim/lazy/kanagawa.nvim,/usr/share/nvim/runtime,/usr/share/nvim/runtime/pack/dist/opt/netrw,/usr/share/nvim/runtime/pack/dist/opt/matchit,/usr/lib64/nvim,~/.local/state/nvim/lazy/readme,~/.local/share/nvim/lazy/cmp_luasnip/after,~/.local/share/nvim/lazy/cmp-cmdline/after,~/.local/share/nvim/lazy/cmp-path/after,~/.local/share/nvim/lazy/cmp-buffer/after,~/.local/share/nvim/lazy/cmp-nvim-lsp/after,~/.local/share/nvim/lazy/mason-lspconfig.nvim/after,~/.local/share/nvim/lazy/indent-blankline.nvim/after
set spelllang=en_us
set spellsuggest=best,9
set statusline=%#lualine_transparent#
set suffixes=.bak,~,.o,.h,.info,.swp,.obj,.snap
set termguicolors
set window=33
" vim: set ft=vim :
