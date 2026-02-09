'use client'

import { useState } from 'react'
import { Play, X } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface VideoModalProps {
  videoId?: string
  buttonClassName?: string
  buttonSize?: 'default' | 'sm' | 'lg' | 'icon'
}

export function VideoModal({ 
  videoId = 'YOUR_DEMO_VIDEO', 
  buttonClassName = '',
  buttonSize = 'lg'
}: VideoModalProps) {
  const [isOpen, setIsOpen] = useState(false)

  // Don't render the button if no real video ID is set
  const hasVideo = videoId && videoId !== 'YOUR_DEMO_VIDEO'

  if (!hasVideo) return null

  return (
    <>
      <Button 
        size={buttonSize} 
        variant="outline" 
        className={buttonClassName}
        onClick={() => setIsOpen(true)}
      >
        <Play className="h-4 w-4" />
        Watch 2-Min Demo
      </Button>

      {/* Modal Overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm animate-in fade-in duration-200"
          onClick={() => setIsOpen(false)}
        >
          <div 
            className="relative mx-4 w-full max-w-3xl animate-in zoom-in-95 duration-200"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Close button */}
            <button
              onClick={() => setIsOpen(false)}
              className="absolute -top-10 right-0 rounded-full p-1.5 text-white/70 hover:text-white transition-colors"
              aria-label="Close video"
            >
              <X className="h-6 w-6" />
            </button>

            {/* Video embed */}
            <div className="relative w-full rounded-xl overflow-hidden shadow-2xl" style={{ paddingBottom: '56.25%' }}>
              <iframe
                className="absolute inset-0 h-full w-full"
                src={`https://www.youtube.com/embed/${videoId}?autoplay=1&rel=0&modestbranding=1`}
                title="DentSignal Demo"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
              />
            </div>

            <p className="text-center text-sm text-white/50 mt-3">
              Press Esc or click outside to close
            </p>
          </div>
        </div>
      )}
    </>
  )
}
