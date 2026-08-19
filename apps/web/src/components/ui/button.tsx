import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

/**
 * Sizes carry more horizontal padding than a typical shadcn button, and the
 * reason is linguistic rather than aesthetic: Indonesian runs 15–20% longer than
 * English for the same meaning. "Cari penerbangan" against "Find flights" is the
 * standing example. Buttons sized to English labels crowd or truncate here.
 */
const buttonVariants = cva(
  "pressable inline-flex items-center justify-center gap-2 whitespace-nowrap font-medium transition-[background-color,border-color,color,box-shadow,transform] disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        primary: "bg-accent text-accent-fg hover:bg-brand-700 dark:hover:bg-brand-300 shadow-card",
        secondary: "bg-surface-2 text-fg hover:bg-surface-3 border border-border",
        outline: "border border-border-strong bg-surface text-fg hover:bg-surface-2",
        ghost: "text-fg-muted hover:bg-surface-2 hover:text-fg",
        link: "text-accent underline-offset-4 hover:underline",
      },
      size: {
        sm: "h-8 px-3 text-xs rounded-md [&_svg]:size-3.5",
        md: "h-10 px-5 text-sm rounded-lg [&_svg]:size-4",
        lg: "h-12 px-7 text-base rounded-lg [&_svg]:size-4.5",
        icon: "h-10 w-10 rounded-lg [&_svg]:size-4",
      },
    },
    defaultVariants: { variant: "primary", size: "md" },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => (
    <button ref={ref} className={cn(buttonVariants({ variant, size }), className)} {...props} />
  ),
);
Button.displayName = "Button";

export { buttonVariants };
