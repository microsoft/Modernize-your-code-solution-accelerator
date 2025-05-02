import * as React from "react";

import { StepProps } from "../../types/types";

export const Step: React.FC<StepProps> = ({ icon, title, status, isLast }) => {
  return (
    <div className="flex flex-wrap gap-8">
      <div className="flex flex-col self-start">
        <img
          loading="lazy"
          src={icon}
          className="object-contain w-6 aspect-[0.22]"
          alt=""
        />
        {isLast && (
          <img
            loading="lazy"
            src={icon}
            className="object-contain w-6 aspect-square"
            alt=""
          />
        )}
      </div>
      <div className="flex flex-col grow shrink-0 basis-0 text-[NeutralForeground1.Rest] w-fit max-md:max-w-full">
        <div className="text-base font-semibold leading-6 max-md:max-w-full">
          {title}
        </div>
        <div className="mt-2 text-sm leading-5 max-md:max-w-full">
          {status}
        </div>
      </div>
    </div>
  );
}