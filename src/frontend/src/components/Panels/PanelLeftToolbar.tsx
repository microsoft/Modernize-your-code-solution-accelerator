import React, { ReactNode } from "react";
import { Body1Strong } from "@fluentui/react-components";
import "./Panels.scss"; // Import for styling

interface PanelLeftToolbarProps {
  panelIcon?: ReactNode;
  panelTitle?: string | null;
  children?: ReactNode;
}

const PanelLeftToolbar: React.FC<PanelLeftToolbarProps> = ({
  panelIcon,
  panelTitle,
  children,
}) => {
  return (
    <div
      className="panelToolbar"
    >
      {(panelIcon || panelTitle) && (
        <div
          className="panelTitle"
        >
          {panelIcon && (
            <div
              className="panelIcon"
            >
              {panelIcon}
            </div>
          )}
          {panelTitle && (
            <Body1Strong
              className="panelSecTitle"
            >
              {panelTitle}
            </Body1Strong>
          )}
        </div>
      )}
      <div
        className="panelTools"
      >
        {children}
      </div>
    </div>
  );
};

export default PanelLeftToolbar;
