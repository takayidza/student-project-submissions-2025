'use client';
import { Button } from '@/components/ui/button'; // shadcn/ui
import { useResizeObserver } from '@wojtekmaj/react-hooks';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import type { PDFDocumentProxy } from 'pdfjs-dist';
import { useCallback, useState } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';

// pdfjs.GlobalWorkerOptions.workerSrc = new URL('pdfjs-dist/build/pdf.worker.min.mjs', import.meta.url).toString();

interface PDFViewerProps {
    file: string; // e.g. document.document_url
    maxWidth?: number;
}

pdfjs.GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

export default function PDFViewer({ file, maxWidth = 800 }: PDFViewerProps) {
    const [numPages, setNumPages] = useState<number>(0);
    const [pageNumber, setPageNumber] = useState<number>(1);
    const [containerRef, setContainerRef] = useState<HTMLElement | null>(null);
    const [containerWidth, setContainerWidth] = useState<number>(maxWidth);

    const onResize = useCallback<ResizeObserverCallback>((entries) => {
        const [entry] = entries;
        if (entry) {
            setContainerWidth(entry.contentRect.width);
        }
    }, []);

    useResizeObserver(containerRef, {}, onResize);

    const onDocumentLoadSuccess = ({ numPages }: PDFDocumentProxy) => {
        setNumPages(numPages);
        setPageNumber(1); // reset to first page
    };

    return (
        <div className="relative">
            {/* Navigation arrows on the sides */}
            <div className="absolute left-0 top-1/2 z-10 -translate-y-1/2 transform">
                <Button
                    variant="outline"
                    size="icon"
                    className="h-10 w-10 rounded-full bg-white/80 shadow-md"
                    onClick={() => setPageNumber((p) => Math.max(p - 1, 1))}
                    disabled={pageNumber <= 1}
                >
                    <ChevronLeft className="h-6 w-6" />
                </Button>
            </div>

            <div className="absolute right-0 top-1/2 z-10 -translate-y-1/2 transform">
                <Button
                    variant="outline"
                    size="icon"
                    className="h-10 w-10 rounded-full bg-white/80 shadow-md"
                    onClick={() => setPageNumber((p) => Math.min(p + 1, numPages))}
                    disabled={pageNumber >= numPages}
                >
                    <ChevronRight className="h-6 w-6" />
                </Button>
            </div>

            {/* Page counter overlay at the bottom */}
            <div className="absolute bottom-4 left-1/2 z-10 -translate-x-1/2 transform rounded-full bg-black/70 px-4 py-1 text-sm text-white">
                Page {pageNumber} of {numPages}
            </div>

            {/* PDF document */}
            <div ref={setContainerRef} className="mx-auto w-full max-w-4xl">
                <Document
                    file={file}
                    onLoadSuccess={onDocumentLoadSuccess}
                    loading={<p className="text-center text-gray-500">Loading document...</p>}
                    error={<p className="text-center text-red-500">Failed to load PDF.</p>}
                >
                    <Page
                        pageNumber={pageNumber}
                        width={containerWidth ? Math.min(containerWidth, maxWidth) : maxWidth}
                        renderAnnotationLayer={false}
                        renderTextLayer={false}
                    />
                </Document>
            </div>
        </div>
    );
}