import React from 'react';
import ReactDiffViewer, {DiffMethod} from 'react-diff-viewer-continued';

interface XmlDiffViewerProps {
    originalXml: string;
    patchedXML: string;
}

const customStyles = {
  variables: {
    dark: {
      diffViewerBackground: '#0f172a',
      addedBackground: '#064e3b',
      addedColor: '#a7f3d0',
      removedBackground: '#7f1d1d',
      removedColor: '#fecaca',
      wordAdded: '#047857',
      wordRemoved: '#991b1b',
      gutterBackground: '#1e293b',
      gutterColor: '#94a3b8',
    },
  },
  line: {
    fontSize: '13px',
    fontFamily: 'monospace',
  },
};

export const XmlDiffViewer: React.FC<XmlDiffViewerProps>=({originalXML,patchedXML}) => {
    if(!originalXml || !patchedXml){
        return (
            <div className="p-4 text-slate-400 bg-slate-900 rounded-lg text-sm">
                No XML data available for diff comparison
            </div>
        );
    
    }

return (
    <div className="rounded-lg overflow-hidden border border-slate-700 shadow-xl">
        <ReactDiffViewer
            oldValue={originalXml}
            newValue={patchedXml}
            splitView={true}
            useDarkTheme={true}
            leftTitle="Original Scenario (.xosc)"
            rightTitle="Patched Scenario (.xosc)"
            compareMethod={DiffMethod.WORDS}
            styles={customStyles}
        />
    </div>
);
};
