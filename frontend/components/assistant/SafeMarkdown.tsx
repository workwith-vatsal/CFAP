'use client';

import React from 'react';

interface SafeMarkdownProps {
  content: string;
  className?: string;
}

export const SafeMarkdown: React.FC<SafeMarkdownProps> = ({
  content,
  className = '',
}) => {
  const parseInline = (text: string): React.ReactNode[] => {
    // Splits text into bold, italic, code, and plain text tokens safely
    const parts: React.ReactNode[] = [];
    let remaining = text;
    let key = 0;

    while (remaining.length > 0) {
      // Bold **text**
      const boldMatch = remaining.match(/^(\*\*|__)(.*?)\1/);
      if (boldMatch) {
        parts.push(
          <strong key={key++} className="font-semibold text-slate-100">
            {boldMatch[2]}
          </strong>
        );
        remaining = remaining.slice(boldMatch[0].length);
        continue;
      }

      // Inline code `code`
      const codeMatch = remaining.match(/^`([^`]+)`/);
      if (codeMatch) {
        parts.push(
          <code
            key={key++}
            className="px-1.5 py-0.5 rounded bg-slate-800 text-indigo-300 font-mono text-xs"
          >
            {codeMatch[1]}
          </code>
        );
        remaining = remaining.slice(codeMatch[0].length);
        continue;
      }

      // Italic *text* or _text_
      const italicMatch = remaining.match(/^(\*|_)(.*?)\1/);
      if (italicMatch && italicMatch[2].length > 0) {
        parts.push(
          <em key={key++} className="italic text-slate-300">
            {italicMatch[2]}
          </em>
        );
        remaining = remaining.slice(italicMatch[0].length);
        continue;
      }

      // Regular text up to the next special markdown token
      const nextSpecial = remaining.search(/(\*\*|__|\*|_|`)/);
      if (nextSpecial === -1) {
        parts.push(<React.Fragment key={key++}>{remaining}</React.Fragment>);
        break;
      } else if (nextSpecial === 0) {
        parts.push(<React.Fragment key={key++}>{remaining[0]}</React.Fragment>);
        remaining = remaining.slice(1);
      } else {
        parts.push(
          <React.Fragment key={key++}>
            {remaining.slice(0, nextSpecial)}
          </React.Fragment>
        );
        remaining = remaining.slice(nextSpecial);
      }
    }

    return parts;
  };

  const renderBlocks = (): React.ReactNode[] => {
    const lines = content.split('\n');
    const nodes: React.ReactNode[] = [];
    let i = 0;

    while (i < lines.length) {
      const line = lines[i];
      const trimmed = line.trim();

      if (!trimmed) {
        i++;
        continue;
      }

      // Headings
      if (trimmed.startsWith('#### ')) {
        nodes.push(
          <h4 key={`h4-${i}`} className="text-sm font-bold text-slate-200 mt-3 mb-1">
            {parseInline(trimmed.slice(5))}
          </h4>
        );
        i++;
        continue;
      }
      if (trimmed.startsWith('### ')) {
        nodes.push(
          <h3 key={`h3-${i}`} className="text-base font-bold text-slate-100 mt-3 mb-1">
            {parseInline(trimmed.slice(4))}
          </h3>
        );
        i++;
        continue;
      }
      if (trimmed.startsWith('## ')) {
        nodes.push(
          <h2 key={`h2-${i}`} className="text-lg font-bold text-indigo-400 mt-4 mb-2">
            {parseInline(trimmed.slice(3))}
          </h2>
        );
        i++;
        continue;
      }
      if (trimmed.startsWith('# ')) {
        nodes.push(
          <h1 key={`h1-${i}`} className="text-xl font-bold text-slate-100 mt-4 mb-2">
            {parseInline(trimmed.slice(2))}
          </h1>
        );
        i++;
        continue;
      }

      // Blockquotes
      if (trimmed.startsWith('> ')) {
        nodes.push(
          <blockquote
            key={`bq-${i}`}
            className="border-l-4 border-indigo-500/50 pl-3 py-1 my-2 bg-indigo-950/20 text-slate-300 text-sm italic rounded-r"
          >
            {parseInline(trimmed.slice(2))}
          </blockquote>
        );
        i++;
        continue;
      }

      // Unordered List (- or *)
      if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
        const listItems: string[] = [];
        while (
          i < lines.length &&
          (lines[i].trim().startsWith('- ') || lines[i].trim().startsWith('* '))
        ) {
          listItems.push(lines[i].trim().slice(2));
          i++;
        }
        nodes.push(
          <ul key={`ul-${i}`} className="list-disc list-inside space-y-1 my-2 text-slate-200">
            {listItems.map((item, idx) => (
              <li key={idx} className="leading-relaxed">
                {parseInline(item)}
              </li>
            ))}
          </ul>
        );
        continue;
      }

      // Ordered List (1. 2.)
      const numMatch = trimmed.match(/^(\d+)\.\s+(.*)/);
      if (numMatch) {
        const listItems: string[] = [];
        while (i < lines.length) {
          const nm = lines[i].trim().match(/^(\d+)\.\s+(.*)/);
          if (!nm) break;
          listItems.push(nm[2]);
          i++;
        }
        nodes.push(
          <ol key={`ol-${i}`} className="list-decimal list-inside space-y-1 my-2 text-slate-200">
            {listItems.map((item, idx) => (
              <li key={idx} className="leading-relaxed">
                {parseInline(item)}
              </li>
            ))}
          </ol>
        );
        continue;
      }

      // Default Paragraph
      nodes.push(
        <p key={`p-${i}`} className="my-1.5 leading-relaxed text-slate-200">
          {parseInline(trimmed)}
        </p>
      );
      i++;
    }

    return nodes;
  };

  return (
    <div className={`space-y-1 text-sm text-slate-200 ${className}`}>
      {renderBlocks()}
    </div>
  );
};
