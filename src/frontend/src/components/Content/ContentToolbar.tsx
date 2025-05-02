import React, { ReactNode } from "react";
import { Body1Strong } from "@fluentui/react-components";
import "./Content.scss"; // Import for styling

interface ContentToolbarProps {
  panelIcon?: ReactNode;
  panelTitle?: string | null;
  children?: ReactNode;
}

const ContentToolbar: React.FC<ContentToolbarProps> = ({
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
              className="panelLabel"
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

export default ContentToolbar;
