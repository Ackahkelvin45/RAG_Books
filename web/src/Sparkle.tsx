// The three four-point stars from the design.
const star = (cx: number, cy: number, r: number) =>
  `M${cx} ${cy - r}C${cx + r * 0.2} ${cy - r * 0.2} ${cx + r * 0.2} ${cy - r * 0.2} ${cx + r} ${cy}` +
  `C${cx + r * 0.2} ${cy + r * 0.2} ${cx + r * 0.2} ${cy + r * 0.2} ${cx} ${cy + r}` +
  `C${cx - r * 0.2} ${cy + r * 0.2} ${cx - r * 0.2} ${cy + r * 0.2} ${cx - r} ${cy}` +
  `C${cx - r * 0.2} ${cy - r * 0.2} ${cx - r * 0.2} ${cy - r * 0.2} ${cx} ${cy - r}Z`

export default function Sparkle({ size = 56, className }: { size?: number; className?: string }) {
  return (
    <svg className={className} width={size} height={size} viewBox="0 0 56 60" fill="currentColor" aria-hidden="true">
      <path d={star(19, 17, 17)} />
      <path d={star(41, 31, 14)} />
      <path d={star(19, 44, 15)} />
    </svg>
  )
}
