interface SearchBarProps {
  value: string
  onChange: (v: string) => void
  sort: string
  onSortChange: (v: string) => void
  typeFilter: string
  onTypeFilterChange: (v: string) => void
}

export default function SearchBar({ value, onChange, sort, onSortChange, typeFilter, onTypeFilterChange }: SearchBarProps) {
  return (
    <div className='flex flex-wrap gap-3 items-center'>
      <div className='relative flex-1 min-w-[200px]'>
        <input
          type='text'
          value={value}
          onChange={e => onChange(e.target.value)}
          placeholder='Search files...'
          className='input-field pl-9'
        />
        <span className='absolute left-3 top-1/2 -translate-y-1/2 text-vault-muted text-sm'>🔍</span>
      </div>
      <select value={sort} onChange={e => onSortChange(e.target.value)} className='input-field w-auto'>
        <option value='created_at'>Newest</option>
        <option value='-created_at'>Oldest</option>
        <option value='display_name'>Name A-Z</option>
        <option value='-display_name'>Name Z-A</option>
        <option value='size_bytes'>Smallest</option>
        <option value='-size_bytes'>Largest</option>
      </select>
      <select value={typeFilter} onChange={e => onTypeFilterChange(e.target.value)} className='input-field w-auto'>
        <option value=''>All types</option>
        <option value='image'>Images</option>
        <option value='video'>Videos</option>
        <option value='audio'>Audio</option>
        <option value='pdf'>PDFs</option>
        <option value='text'>Text</option>
        <option value='zip'>Archives</option>
      </select>
    </div>
  )
}
