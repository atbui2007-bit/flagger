import { useCallback, useEffect, useId, useMemo, useRef, useState } from 'react'

type Option = { value: string; label: string }

type FilterSelectProps = {
  label: string
  value: string
  options: Option[]
  onChange: (value: string) => void
}

type PopoverElement = HTMLDivElement & {
  showPopover?: () => void
  hidePopover?: () => void
}

type ToggleLikeEvent = Event & {
  newState?: 'open' | 'closed'
}

function normalizeId(value: string) {
  return value.replace(/[^a-zA-Z0-9_-]/g, '-')
}

function nextIndexByPrefix(options: Option[], currentIndex: number, prefix: string) {
  const normalizedPrefix = prefix.toLocaleLowerCase()
  const repeatedCharacter = normalizedPrefix.length > 1 && normalizedPrefix.split('').every((character) => character === normalizedPrefix[0])
  const normalized = repeatedCharacter ? normalizedPrefix[0] : normalizedPrefix
  const startOffset = normalizedPrefix.length === 1 || repeatedCharacter ? 1 : 0
  for (let offset = startOffset; offset < options.length + startOffset; offset += 1) {
    const index = (currentIndex + offset + options.length) % options.length
    if (options[index]?.label.toLocaleLowerCase().startsWith(normalized)) return index
  }
  return currentIndex
}

function FilterSelect({ label, value, options, onChange }: FilterSelectProps) {
  const reactId = useId()
  const idBase = normalizeId(reactId)
  const labelId = `${idBase}-label`
  const valueId = `${idBase}-value`
  const popId = `${idBase}-popover`
  const triggerRef = useRef<HTMLButtonElement | null>(null)
  const popRef = useRef<PopoverElement | null>(null)
  const listRef = useRef<HTMLDivElement | null>(null)
  const wasOpenRef = useRef(false)
  const typeaheadRef = useRef('')
  const typeaheadTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const [open, setOpen] = useState(false)
  const selectedIndex = Math.max(0, options.findIndex((option) => option.value === value))
  const [activeIndex, setActiveIndex] = useState(selectedIndex)
  const selectedLabel = options[selectedIndex]?.label ?? options[0]?.label ?? label
  const activeId = options[activeIndex] ? `${idBase}-option-${activeIndex}` : undefined

  const positionPopover = useCallback(() => {
    const trigger = triggerRef.current
    const popover = popRef.current
    if (!trigger || !popover) return

    const rect = trigger.getBoundingClientRect()
    const clearsBelow = window.innerHeight - rect.bottom >= 324
    popover.style.left = `${Math.max(8, rect.left)}px`
    popover.style.minWidth = `${rect.width}px`
    popover.style.maxWidth = `calc(100vw - ${Math.max(16, rect.left + 8)}px)`
    popover.style.top = clearsBelow ? `${rect.bottom + 4}px` : ''
    popover.style.bottom = clearsBelow ? '' : `${Math.max(8, window.innerHeight - rect.top + 4)}px`
  }, [])

  const scrollActiveIntoView = useCallback((index: number) => {
    window.requestAnimationFrame(() => {
      document.getElementById(`${idBase}-option-${index}`)?.scrollIntoView({ block: 'nearest' })
    })
  }, [idBase])

  const closePopover = useCallback(() => {
    popRef.current?.hidePopover?.()
  }, [])

  const selectOption = useCallback((option: Option) => {
    onChange(option.value)
    closePopover()
  }, [closePopover, onChange])

  const moveActive = useCallback((nextIndex: number) => {
    const boundedIndex = Math.min(Math.max(nextIndex, 0), options.length - 1)
    setActiveIndex(boundedIndex)
    scrollActiveIntoView(boundedIndex)
  }, [options.length, scrollActiveIntoView])

  useEffect(() => {
    if (!open) return undefined

    // ponytail: close on scroll instead of tracking the anchor - matches native select; add anchor tracking only if a sticky-scroll case appears.
    const closeOnViewportChange = () => closePopover()
    window.addEventListener('scroll', closeOnViewportChange, true)
    window.addEventListener('resize', closeOnViewportChange)
    return () => {
      window.removeEventListener('scroll', closeOnViewportChange, true)
      window.removeEventListener('resize', closeOnViewportChange)
    }
  }, [closePopover, open])

  useEffect(() => () => {
    if (typeaheadTimerRef.current) clearTimeout(typeaheadTimerRef.current)
  }, [])

  useEffect(() => {
    if (!open) setActiveIndex(selectedIndex)
  }, [open, selectedIndex])

  const optionNodes = useMemo(() => options.map((option, index) => (
    <div
      role="option"
      id={`${idBase}-option-${index}`}
      key={option.value}
      aria-selected={option.value === value}
      className={`filter-option${index === activeIndex ? ' active' : ''}`}
      onClick={() => selectOption(option)}
      onMouseMove={() => setActiveIndex(index)}
    >
      <svg className="filter-option-check" viewBox="0 0 16 16" aria-hidden="true">
        <path d="M3.5 8.2 6.6 11 12.5 5" />
      </svg>
      <span>{option.label}</span>
    </div>
  )), [activeIndex, idBase, options, selectOption, value])

  return (
    <div className="filter-pill" data-active={value !== ''}>
      <span id={labelId} className="sr-only">{label}</span>
      <button
        type="button"
        className="filter-pill-trigger"
        ref={triggerRef}
        {...{ popovertarget: popId }}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-labelledby={`${labelId} ${valueId}`}
      >
        <span id={valueId}>{selectedLabel}</span>
        <svg className="filter-caret" viewBox="0 0 12 8" aria-hidden="true">
          <path d="M2 2 6 6 10 2" />
        </svg>
      </button>

      <div
        id={popId}
        {...{ popover: 'auto' }}
        className="filter-popover"
        ref={popRef}
        onBeforeToggle={(event) => {
          const nativeEvent = event.nativeEvent as ToggleLikeEvent
          if (nativeEvent.newState === 'open') positionPopover()
        }}
        onToggle={(event) => {
          const nativeEvent = event.nativeEvent as ToggleLikeEvent
          const nextOpen = nativeEvent.newState === 'open'
          setOpen(nextOpen)
          if (nextOpen) {
            const nextActive = Math.max(0, options.findIndex((option) => option.value === value))
            setActiveIndex(nextActive)
            window.requestAnimationFrame(() => {
              popRef.current?.focus()
              scrollActiveIntoView(nextActive)
            })
          } else if (wasOpenRef.current) {
            triggerRef.current?.focus()
          }
          wasOpenRef.current = nextOpen
        }}
        onKeyDown={(event) => {
          if (event.key === 'ArrowDown') {
            event.preventDefault()
            moveActive(activeIndex + 1)
          } else if (event.key === 'ArrowUp') {
            event.preventDefault()
            moveActive(activeIndex - 1)
          } else if (event.key === 'Home') {
            event.preventDefault()
            moveActive(0)
          } else if (event.key === 'End') {
            event.preventDefault()
            moveActive(options.length - 1)
          } else if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault()
            const option = options[activeIndex]
            if (option) selectOption(option)
          } else if (event.key === 'Tab') {
            closePopover()
          } else if (event.key.length === 1 && /\S/.test(event.key)) {
            typeaheadRef.current += event.key
            if (typeaheadTimerRef.current) clearTimeout(typeaheadTimerRef.current)
            typeaheadTimerRef.current = setTimeout(() => { typeaheadRef.current = '' }, 600)
            event.preventDefault()
            moveActive(nextIndexByPrefix(options, activeIndex, typeaheadRef.current))
          }
        }}
        tabIndex={-1}
        role="listbox"
        aria-label={label}
        aria-activedescendant={activeId}
      >
        <div className="filter-popover-list" ref={listRef}>
          {optionNodes}
        </div>
      </div>
    </div>
  )
}

export default FilterSelect
